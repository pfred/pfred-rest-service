package tst.pfred.rest.service;

import org.junit.Before;
import org.junit.Test;

import junit.framework.Assert;
import org.pfred.rest.service.InfoResource;

public class InfoResourceTest {

    private InfoResource resource;

    @Before
    public void setUp() throws Exception {
        resource = new InfoResource();
    }

    @Test
    public void testGetVersion() {
        String expected = "1.0.0";
        String result = resource.getVersion();
        System.out.println("Version: " + result);
        Assert.assertEquals(expected, result);
    }
}
