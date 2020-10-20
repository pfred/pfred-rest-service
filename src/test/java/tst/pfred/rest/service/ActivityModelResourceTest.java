package tst.pfred.rest.service;

import javax.ws.rs.core.Response;
import javax.ws.rs.core.Response.Status;

import org.junit.Before;
import org.junit.Test;

import junit.framework.Assert;
import org.pfred.rest.service.ActivityModelResource;

public class ActivityModelResourceTest {

    private ActivityModelResource resource;

    @Before
    public void setUp() throws Exception {
        resource = new ActivityModelResource();
    }

    @Test
    public void testRunSirnaActivityModel() {
        String primarySequence = "AGUCAUUUC";
        String rundir = "test_siRNA";
        // Response response = resource.runSirnaActivityModel(primarySequence, rundir);

        // System.out.println("Result: " + response.getEntity());

        // if (response.getStatusInfo() == Status.OK) {
        //     Assert.assertTrue(true);
        // } else {
        //     Assert.assertTrue(false);
        // }
    }

    @Test
    public void testRunAsoActivityModel() {
        String primarySequence = "AGUCAUUUC";
        int oligoLength = 18;
        String rundir = "test_siRNA";
        // Response response = resource.runAsoActivityModel(primarySequence, rundir, oligoLength);

        // System.out.println("Result: " + response.getEntity());

        // if (response.getStatusInfo() == Status.OK) {
        //     Assert.assertTrue(true);
        // } else {
        //     Assert.assertTrue(false);
        // }
    }
}
