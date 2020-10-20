# Run with scrapy runspider ensembl_rest_spider.py -o ensembl_rest_endpoints.json

import scrapy
import json


ensembl_rest_url = 'https://rest.ensembl.org'



class EnsemblRESTSpider(scrapy.Spider):
    """
    Spider to extract data from the Ensembl REST API documentation.
    """
    name = "ensembl_rest"

    custom_settings = {
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],
        'RETRY_TIMES': 10,
        'DOWNLOAD_DELAY': 1
    }

    
    start_urls = [ensembl_rest_url]
    
    def parse(self, response):
        """Extract the API endpoints data from the webpage.
        
        The information we need for each REST endpoint is:
            - Endpoint url structure.
            - Endpoint description.
            - Endpoint documentation webpage.
        """        
        endpoints = self.endpoint_links(response)
        print(len(endpoints), '\n'*10)
        for endpoint_link, category in endpoints:
            yield response.follow(endpoint_link, 
                                  callback=self.parse_endpoint,
                                  meta={'category':category})
        
    # ---
    
    def endpoint_links(self, response):
        "Return a list of the fully extracted endpoints with their associated categories."

        rows = response.xpath('//table/child::node()')

        # Category headers come mixed with the actual endpoint rows
        current_category = None
        links = []
        for item in rows:
            if 'thead' in item.extract():
                current_category = item.xpath('.//h3/text()').get().strip()

            elif 'tr' in item.extract():
                category_links = item.xpath('.//a/@href').extract()
                links.extend((link, current_category) for link in category_links)

        return links
    # ---
    
    def parse_endpoint(self, response):
        "Unpack the information for the endpoint."

        required_parameters = self.parse_endpoint_parameters(
                                response,
                                'Required'
                              )
        optional_parameters = self.parse_endpoint_parameters(
                                response,
                                'Optional'
                              )
        parameters = {
            'required': required_parameters,
            'optional': optional_parameters
        }

        return {
            'name': response.url.split('/').pop(),
            'resource_string': response.xpath('//h1/text()').get(),
            'category': response.meta['category'],
            'description': response.xpath('//p/text()').extract_first(),
            'parameters': parameters,
            'resource_info': self.parse_resource_info(response),
            'documentation_url': response.url
        }
    # ---

    def parse_endpoint_parameters(self, response, parameter_type):
        # Parameter type can be 'Required' or 'Optional'
        # Find the table that describes the required parameters
        params_table = response.xpath(
                        f"//h3[text()='{parameter_type}']/following::table"
                       )[0]
        # Parse the parameters from the table
        params_table_header = self.parse_table_header(params_table)
        table_rows = self.parse_table_rows(params_table.css('tr')[1:]) # omit header row

        # Clean the data
        parameters = []
        for values in table_rows:
            
            # Handle the case of multiple example values
            n_fields = len(params_table_header)
            if len(values) != n_fields:
                values = values[:n_fields-1] + ', '.join(values[n_fields-1:])

            parameter = dict(zip(params_table_header, values))
            parameters.append(parameter)

        return parameters
    # ---

    def parse_table_header(self, table):
        return table.css('th::text').extract()
    
    def parse_table_rows(self, table_rows):
        rows = []
        for row in table_rows: # Remove the header

            values = []
            for item in row.css('td'):
                # Handle the different nestings of the data
                if item.re('var'):
                    selector = 'var::text'
                else:
                    selector = 'td::text'
                value = item.css(selector).extract()

                # Cleanup
                value = ', '.join(value) if value else ''
                value = value.strip()

                values.append(value)

            rows.append(values)

        return rows
    # ---

    def parse_resource_info(self, response):
        rinfo_table = response.xpath(
                        "//h3[text()='Resource Information']/following::table"
                      )[0]

        resource_info = {}
        for row in rinfo_table.css('tr'):
            # Parse the row
            data = row.css('td::text').extract()
            # Every row is key, value, value...
            resource_info[data[0]] = ', '.join(data[1:])

        return resource_info
    # ---


