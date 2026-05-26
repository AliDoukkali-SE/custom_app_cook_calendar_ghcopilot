targetScope = 'resourceGroup'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base app name used in resource naming')
@minLength(3)
param appName string

@description('Container image tag for meal-calendar image in ACR')
@minLength(1)
param imageTag string

@description('Enable Cosmos DB free tier. Some subscription types do not support it.')
param cosmosEnableFreeTier bool = false

var suffix = uniqueString(resourceGroup().id)
var sanitizedAppName = toLower(replace(appName, '-', ''))
var logAnalyticsName = 'law-${appName}-${suffix}'
var appInsightsName = 'appi-${appName}-${suffix}'
var containerEnvName = 'cae-${appName}-${suffix}'
var cosmosAccountName = toLower(take('cosmos-${appName}-${suffix}', 44))
var acrName = toLower(take('acr${sanitizedAppName}${suffix}', 50))
var containerAppName = 'meal-calendar'
var imageName = '${acr.properties.loginServer}/meal-calendar:${imageTag}'
var cosmosTableEndpoint = 'https://${cosmosAccountName}.table.cosmos.azure.com:443/'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    capabilities: [
      {
        name: 'EnableServerless'
      }
      {
        name: 'EnableTable'
      }
    ]
    enableFreeTier: cosmosEnableFreeTier
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
  }
}

resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'meal-calendar'
          image: imageName
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            {
              name: 'COSMOS_TABLE_ENDPOINT'
              value: cosmosTableEndpoint
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output acrLoginServer string = acr.properties.loginServer

// Grant the Container App's managed identity data-plane access to the
// Cosmos DB for Table account using the built-in
// "Cosmos DB Built-in Data Contributor" role
// (00000000-0000-0000-0000-000000000002).
resource cosmosMealsTable 'Microsoft.DocumentDB/databaseAccounts/tables@2024-05-15' = {
  parent: cosmos
  name: 'meals'
  properties: {
    resource: {
      id: 'meals'
    }
  }
}

resource cosmosTableDataContributor 'Microsoft.DocumentDB/databaseAccounts/tableRoleAssignments@2024-12-01-preview' = {
  parent: cosmos
  name: guid(cosmos.id, containerApp.id, 'cosmos-table-data-contributor')
  properties: {
    roleDefinitionId: '${cosmos.id}/tableRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: containerApp.identity.principalId
    scope: cosmos.id
  }
}
