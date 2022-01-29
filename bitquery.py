# %%
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from dotenv import dotenv_values

# %%
transport = RequestsHTTPTransport(
    url='https://graphql.bitquery.io/',
    verify=True,
    retries=3,
    headers={'X-API-KEY': dotenv_values()['BITQUERY_API']})

client = Client(transport=transport, fetch_schema_from_transport=True)
# %%
query = gql('''
{
  ethereum(network: ethereum) {
    dexTrades(
      date: {is:"2020-11-01"}
      exchangeName: {is: "Uniswap"}, 
      baseCurrency: {is: "0xdac17f958d2ee523a2206206994597c13d831ec7"}, 
      quoteCurrency: {is: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"}) {
     
    
      baseCurrency {
        symbol
        address
      }
      baseAmount
      quoteCurrency {
        symbol
        address
      }
      quoteAmount
      
      trades: count
      quotePrice
      
      side
  
    }
  }
}
    ''')
print(client.execute(query))
# %%
