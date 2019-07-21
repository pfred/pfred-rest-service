package org.pfred.rest.service;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import javax.ws.rs.QueryParam;

@Path("ActivityModel")
@Api(value = "Activity Model")
public class ActivityModelResource {

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "siRNA")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run siRNA activity model successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running siRNA activity model")})
    @ApiOperation(value = "Run siRNA Activity Model")
    public Response runSirnaActivityModel(@ApiParam(value = "Primary Sequence", required = true) @QueryParam("PrimarySequence") final String primarySequence) {
        try {
            //TODO
            String result = "INPUT:"+ primarySequence;
            return Response.status(Response.Status.OK).entity(result).build();
        } catch (Exception ex) {
            return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
        }
    }

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "ASO")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run ASO activity model successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running ASO activity model")})
    @ApiOperation(value = "Run ASO Activity Model")
    public Response runAsoActivityModel(@ApiParam(value = "Primary Sequence", required = true) @QueryParam("PrimarySequence") final String primarySequence,
            @ApiParam(value = "Oligonucleotide Length", required = true) @QueryParam("OligoLength") final Integer oligoLength) {
        try {
            //TODO
            String result = "INPUT:"+primarySequence + " "+ oligoLength;
            return Response.status(Response.Status.OK).entity(result).build();
        } catch (Exception ex) {
            return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
        }
    }

}
