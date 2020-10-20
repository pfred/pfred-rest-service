# Run with scrapy runspider ensembl_rest_spider.py

import scrapy
import json


response_codes_url = 'https://github.com/Ensembl/ensembl-rest/wiki/HTTP-Response-Codes'


class ResponseCodesSpider(scrapy.Spider):
    
    name = "ensembl_rest_response_codes"
    
    start_urls = [
        response_codes_url
    ]
    
    def parse(self, response):
        """Extract the response codes data from the documentation.
        
        The information we need for each response code is:
            - Code. Numeric code.
            - Name. Long name of the response code.
            - Description.
        """
        response_codes = self.parse_response_codes(response)
        
        with open('ensembl_response_codes.json', 'w') as outf:
            json.dump(response_codes, outf, indent=2)
    # ---
    
    def parse_response_codes(self, response):
        "Extract the important data on the response codes."
        extract_code = lambda raw_code: (
            raw_code.css('td').css('::text').extract()
        )
        
        raw_codes = response.css('tr')[1:]
        
        response_codes = dict()
        for raw_code in raw_codes:
            code, name, *description = extract_code(raw_code)
            description = ''.join(description)
            
            response_codes[code] = {
                'name' : name,
                'description' : description
            }
            
        return response_codes
    # ---
