package org.pfred.rest.service;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;

@Path("Info")
@Api(value = "Info")
public class InfoResource {

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    @Path(value="Version")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Fetching service version completed successfully"),
        @ApiResponse(code = 400, message = "Error occured fetching service version"),})
    @ApiOperation(value = "Fetch service version")
    public String getVersion() {
        return "1.0.0";
    }
}
