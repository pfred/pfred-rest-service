package org.pfred.rest.service;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.logging.Logger;
import java.io.File;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import javax.ws.rs.QueryParam;
import org.pfred.rest.service.ShellUtilities;

@Path("ScriptUtilities")
@Api(value = "Script Utilities")
public class ScriptUtilitiesResource {

    private static Logger logger = Logger.getLogger(ScriptUtilitiesResource.class.getName());

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "Orthologs")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run get Orthologs successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running get Orthologs")})
    @ApiOperation(value = "Run get Orthologs")
    public Response getOrthologs(@ApiParam(value = "Ensembl ID", required = true) @QueryParam("enseblID") final String enseblID,
            @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName,
            @ApiParam(value = "Requested Species", required = true) @QueryParam("RequestedSpecies") final String requestedSpecies,
            @ApiParam(value = "Species", required = true) @QueryParam("Species") final String species) {

        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);
        String command = "getOrthologs.sh  " + enseblID + " " + species + " " + requestedSpecies;

        boolean success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);

        if (success) {
            logger.info("Shell command run successfully");
            String outputFilePath = fullRunDirectory + "/seqAnnotation.csv";
            try {
                String result = ShellUtilities.readFileAsString(outputFilePath);
                return Response.status(Response.Status.OK).entity(result).build();
            } catch (Exception ex) {
                return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
            }
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "enumerate_first")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run enumerate successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running enumerate")})
    @ApiOperation(value = "Run enumerate")
    public Response enumerate_first(@ApiParam(value = "Secondary Transcript IDs", required = true) @QueryParam("SecondaryTranscriptIDs") final String secondaryTranscriptIDs,
            @ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName,
            @ApiParam(value = "Primary transcript ID", required = true) @QueryParam("PrimaryTranscriptID") final String primaryTranscriptID,
            @ApiParam(value = "OligonLen", required = true) @QueryParam("oligoLen") final String oligoLen) {
        String shellScript = "Enumeration.sh";
        String outputFile = "EnumerationResult.csv";

        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);

        String command = shellScript + " " + secondaryTranscriptIDs + " " + primaryTranscriptID + " " + oligoLen + "";

        boolean success = ShellUtilities.runCommandThroughShell(command, fullRunDirectory);

        if (success) {
            logger.info("Shell command run successfully");
            try {
                String results = ShellUtilities.readFileAsString(fullRunDirectory + "/" + outputFile);
                return Response.status(Response.Status.OK).entity(results).build();
            } catch (Exception ex) {
                return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
            }
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }

    // This ONLY collects data from sequence.fa once "enumerate_first" was run.

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "enumerate_second")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run enumerate successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running enumerate")})
    @ApiOperation(value = "Run enumerate")
    public Response enumerate_second(@ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName) {
        String seqFile = "sequence.fa";
        String fullRunDirectory = ShellUtilities.prepareRunDir(runName);

        try {
            File seqF = new File(fullRunDirectory + "/" + seqFile);
            if(seqF.length() == 0){
                return Response.status(Response.Status.OK).entity("sequence.fa is empty").build();
            }
            String results = ShellUtilities.readFileAsString(fullRunDirectory + "/" + seqFile);
            return Response.status(Response.Status.OK).entity(results).build();
        } catch (Exception ex) {
            return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
        }
    }

    @GET
    @Produces(value = MediaType.TEXT_PLAIN)
    @Path(value = "clean")
    @ApiResponses(value = {
        @ApiResponse(code = 200, message = "Run clean running directory successfully"),
        @ApiResponse(code = 400, message = "Error occurred in running clean running directory")})
    @ApiOperation(value = "Run clean run directory")
    public Response cleanRunDir(@ApiParam(value = "Run Directory", required = true) @QueryParam("RunDirectory") final String runName){
        String fullRunDirectory = ShellUtilities.getRunDir() + '/' + runName;

        try {
            boolean success = ShellUtilities.removeDir(fullRunDirectory);
            if(success) {
                String result = "Run directory removed";
                return Response.status(Response.Status.OK).entity(result).build();
            }
        } catch (Exception ex) {
            return Response.status(Response.Status.BAD_REQUEST).entity(ex.getMessage()).build();
        }
        return Response.status(Response.Status.BAD_REQUEST).entity("Shell command run failed").build();
    }
}
