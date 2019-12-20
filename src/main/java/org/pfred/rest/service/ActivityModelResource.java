package org.pfred.rest.service;

import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.Consumes;
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

@Path("ActivityModel")
@Api(value = "Activity Model")
public class ActivityModelResource {

    private static Logger logger = Logger.getLogger(ActivityModelResource.class.getName());

    @POST
    @Consumes(value = MediaType.TEXT_PLAIN)
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "siRNA")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run siRNA activity model successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running siRNA activity model")})
    @ApiOperation(value = "Run siRNA Activity Model")
    public Response runSirnaActivityModel(@ApiParam(value = "Primary ID", required = true) @QueryParam("PrimaryID") final String primaryID,
            @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName) {
        String shellScript = "siRNAActivityModel.sh";
        String outputFile = "siRNAActivityModelResult.csv";
        // String targetFile = "target.txt";

        String scriptsDirectory = ShellUtilities.getScriptsDir();
        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);

        String command = "getSeqGivenTrans.sh " + primaryID;
        logger.info(command);
        boolean success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);

        if (success){
            logger.info("Shell command run successfully");
            ShellUtilities.copyFile(scriptsDirectory + "/siRNA_2431seq_modelBuilding.csv", fullRunDirectory);
            // ShellUtilities.saveStringAsFile(fullRunDirectory + "/" + targetFile, primaryID);

            command = shellScript;
            success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);

            if (success) {
                logger.info("Shell command run successfully");
                try {
                    String result = ShellUtilities.readFileAsString(fullRunDirectory + "/" + outputFile);
                    return Response.status(Response.Status.OK).entity(result).build();
                } catch (Exception ex) {
                    return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
                }
            }
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }

    @POST
    @Consumes(value = MediaType.TEXT_PLAIN)
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "ASO")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run ASO activity model successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running ASO activity model")})
    @ApiOperation(value = "Run ASO Activity Model")
    public Response runAsoActivityModel(@ApiParam(value = "Primary ID", required = true) @QueryParam("PrimaryID") final String primaryID,
            @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName,
            @ApiParam(value = "Oligonucleotide Length", required = true) @QueryParam("OligoLength") final Integer oligoLength) {
        //TODO: OligoLength is not being used in this function
        String shellScript = "ASOActivityModel.sh";
        String outputFile = "ASOActivityModelResult.csv";
        // String targetFile = "target.txt";

        String scriptsDirectory = ShellUtilities.getScriptsDir();
        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);

        String command = "getSeqGivenTrans.sh " + primaryID;
        boolean success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);
        // ShellUtilities.saveStringAsFile(fullRunDirectory + "/"+targetFile, primaryID);

        if (success){
            logger.info("Shell command run successfully");


            ShellUtilities.copyFile(scriptsDirectory + "/input_15_21_100_1000_12.txt", fullRunDirectory);
            ShellUtilities.copyFile(scriptsDirectory + "/AOBase_542seq_cleaned_modelBuilding_Jan2009_15_21_noOutliers.csv", fullRunDirectory);

            command = shellScript;

            success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);

            if (success) {
                logger.info("Shell command run successfully");
                try {
                    String result = ShellUtilities.readFileAsString(fullRunDirectory + "/" + outputFile);
                    return Response.status(Response.Status.OK).entity(result).build();
                } catch (Exception ex) {
                    return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
                }
            }
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }
}
