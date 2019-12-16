package org.pfred.rest.service;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.logging.Logger;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import javax.ws.rs.QueryParam;
import org.pfred.rest.service.ShellUtilities;

@Path("OffTargetSearch")
@Api(value = "Off Target Search")
public class OffTargetSearchResource {

    private static Logger logger = Logger.getLogger(OffTargetSearchResource.class.getName());

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "siRNA")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run siRNA off target search successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running siRNA off target search")})
    @ApiOperation(value = "Run siRNA Off Target Search")
    public Response runSirnaOffTargetSearch(@ApiParam(value = "species", required = true) @QueryParam("Species") final String species,
            @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName,
            @ApiParam(value = "IDs", required = true) @QueryParam("IDs") final String IDs,
            @ApiParam(value = "missMatches", required = true) @QueryParam("missMatches") final String missMatches) {
        String shellScript = "siRNAOffTargetSearch.sh";
        String outputFile = "siRNAOffTargetSearchResult.csv";
        String targetFile = "target.txt";

        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);
        String command = shellScript + " " + species + " " + IDs + " " + missMatches;

        boolean success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);

        if (success) {
            logger.info("Shell command run successfully");
            try {
                String result = ShellUtilities.readFileAsString(fullRunDirectory + "/" + outputFile);
                return Response.status(Response.Status.OK).entity(result).build();
            } catch (Exception ex) {
                return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
            }
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "ASO")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run ASO off target search successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running ASO off target search")})
    @ApiOperation(value = "Run ASO Off Target Search")
    public Response runAsoOffTargetSearch(@ApiParam(value = "species", required = true) @QueryParam("Species") final String species,
            @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName,
            @ApiParam(value = "IDs", required = true) @QueryParam("IDs") final String IDs,
            @ApiParam(value = "missMatches", required = true) @QueryParam("missMatches") final String missMatches) {
        String shellScript = "ASOOffTargetSearch.sh";
        String outputFile = "ASOOffTargetSearchResult.csv";
        boolean success = false;


        // String OFILE="antisenseOffTarget.out";
        // shellScript = "asDNA_OffTargetSearch_bowtie.pl";
        // asDNA_OffTargetSearch_bowtie.pl -s "$1" -g "$2" -t $type  -v "$3" $IFILE > $OFILE
        // String command = shellScript + " -s " + species + " -g " + IDs + " -t sense -v " + missMatches + " test.txt >" + OFILE;


        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);
        String command = shellScript + " " + species + " " + IDs + " " + missMatches;

        // This is cheating. We acknowledge empty species as a complete run result, just get the data, don't run the shell script

        logger.info(species);

        if (species == "paco"){
            logger.info("Shell command Avoided, skipping...");
            success = true;
        }else{
            success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);
        }

        if (success) {
            logger.info("Shell command run successfully");
            try {
                String result = ShellUtilities.readFileAsString(fullRunDirectory + "/" + outputFile);
                return Response.status(Response.Status.OK).entity(result).build();
            } catch (Exception ex) {
                return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
            }
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "Check")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run Check file existence successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running Check file existence")})
    @ApiOperation(value = "Run Check file existence")
    public Response runCheckFile(@ApiParam(value = "file", required = true) @QueryParam("File") final String file,
                                          @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName){
        String outputFile = file;
        boolean success = false;

        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);

        logger.info(file);

        try {
            String result = ShellUtilities.readFileAsString(fullRunDirectory + "/" + outputFile);
            logger.info(result);
            return Response.status(Response.Status.OK).entity(result).build();
        } catch (Exception ex) {
            return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
        }
    }
}
