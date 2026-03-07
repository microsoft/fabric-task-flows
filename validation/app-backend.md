# Validation Checklist

Post-deployment validation for App Backend task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| SQL Database | Create tables/schema, configure security (RLS/OLS if needed), verify OneLake mirroring |
| Cosmos DB | Create containers, configure partition keys, load sample data, verify OneLake mirroring |
| GraphQL API | Select data sources, choose tables/views to expose, define relationships, test queries |
| User Data Functions | Write function code, add PyPI libraries, publish functions, test with sample inputs |
| Variable Library | Add variables, create value sets per stage, set active value set, configure item references |
| Semantic Model | Configure connection to database (via OneLake mirror), set query mode (Direct Lake / DirectQuery) |
| Report | Connect to Semantic Model, build visualizations, configure refresh |
| Data Agent | Add data sources (up to 5), select tables, write instructions, add example queries |
| Ontology | Define entity types/properties/relationships, bind to data sources, refresh graph |

## Checklist

### Phase 1: Foundation

- [ ] SQL Database OR Cosmos DB exists in workspace
- [ ] Database is accessible (connection test succeeds)
- [ ] Tables/containers are created with correct schema
- [ ] Sample data is loaded for testing
- [ ] OneLake mirroring is active (data visible in Delta format)
- [ ] SQL analytics endpoint is available (for SQL Database)
- [ ] Cross-database queries work from SQL analytics endpoint

### Phase 1b: Configuration (if Variable Library used)

- [ ] Variable Library item exists in workspace
- [ ] Variables are defined with correct types and default values
- [ ] Value sets exist for each deployment stage (Dev/PPE/Prod)
- [ ] Active value set is correct for current workspace
- [ ] Item reference variables point to correct workspace + item IDs
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 2: API Layer

#### GraphQL API

- [ ] GraphQL API item exists in workspace
- [ ] Data source(s) connected (SQL Database, Cosmos DB, or Lakehouse SQL endpoint)
- [ ] Schema auto-generated with expected types and fields
- [ ] Relationships defined between related entities (if applicable)
- [ ] Test query returns expected results in built-in editor
- [ ] Mutations work for write operations (via stored procedures if SQL Database)
- [ ] Endpoint URL is accessible and returns valid responses
- [ ] Permissions are configured (who can query the API)

#### User Data Functions

- [ ] User Data Functions item exists in workspace
- [ ] Required PyPI libraries are installed (pandas, requests, etc.)
- [ ] All functions have `@udf.function()` decorator
- [ ] Functions are published (no pending changes indicator)
- [ ] Each function tested with sample inputs in Run Only mode
- [ ] REST endpoints are accessible from external HTTP clients
- [ ] Functions that write to database successfully persist data
- [ ] Error handling returns meaningful error messages

### Phase 3: Analytics (Optional)

- [ ] Semantic Model exists and is connected to database (via OneLake mirror)
- [ ] Query mode is configured (Direct Lake for optimal performance)
- [ ] Measures and relationships are defined
- [ ] Data refresh succeeds (or Direct Lake auto-refreshes)
- [ ] Semantic Model is accessible to report consumers

### Phase 4: Consumption (Optional)

#### Report

- [ ] Report exists and is connected to Semantic Model
- [ ] Visualizations render with correct data
- [ ] Filters and slicers work as expected
- [ ] Report is shared with intended audience

#### Data Agent

- [ ] Data Agent item exists in workspace
- [ ] Data sources added (up to 5)
- [ ] Relevant tables selected in explorer
- [ ] Custom instructions configured (if applicable)
- [ ] Example queries added for few-shot learning (if applicable)
- [ ] Test questions return accurate, data-backed answers
- [ ] Generated SQL/DAX/KQL queries are correct

#### Ontology (if used)

- [ ] Ontology item exists in workspace
- [ ] Entity types defined with properties and relationships
- [ ] Data bindings configured to OneLake sources
- [ ] Graph model refreshed and visualized
- [ ] NL2Ontology queries return expected results
