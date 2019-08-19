package org.pfred.rest.service;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.logging.Level;
import java.util.logging.Logger;


public class ShellUtilities{

    private static Logger logger = Logger.getLogger(ShellUtilities.class.getName());
    private static String runDirectory = System.getenv("RUN_DIR");
    private static String scriptsDirectory = System.getenv("SCRIPTS_DIR");

    public static boolean runCommandThroughShell(String command, String directory) {
        logger.log(Level.INFO, "Running Shell Command: " + command);
        File wd = new File("/bin");
        Process proc = null;
        try {
            proc = Runtime.getRuntime().exec("/bin/bash", null, wd);
        } catch (IOException ex) {
            logger.log(Level.SEVERE, "Error executing /bin/bash", ex);
            return false;
        }
        if (proc != null) {
            BufferedReader in = new BufferedReader(new InputStreamReader(proc.getInputStream()));
            PrintWriter out = new PrintWriter(new BufferedWriter(new OutputStreamWriter(proc.getOutputStream())), true);

            System.out.println(out.toString());

            out.println("cd " + directory);

            out.println(command);
            out.println("exit");
            out.flush();
            try {
                Thread.sleep(5000);
            } catch (InterruptedException ex) {
                logger.log(Level.SEVERE, null, ex);
            }
            try {
                String line = in.readLine();
                while (line != null) {
                    line = in.readLine();
                    Thread.sleep(1);
                }
                proc.waitFor();
                in.close();
                out.close();
                proc.destroy();
            } catch (Exception ex) {
                logger.log(Level.SEVERE, "Error executing command line in bash shell", ex);
                return false;
            }
        }
        return true;
    }

    public static String readFileAsString(String filePath) throws java.io.IOException {
        StringBuffer fileData = new StringBuffer(1000);
        BufferedReader reader = new BufferedReader(new FileReader(filePath));
        char[] buf = new char[1024];
        int numRead = 0;
        while ((numRead = reader.read(buf)) != -1) {
            String readData = String.valueOf(buf, 0, numRead);
            fileData.append(readData);
            buf = new char[1024];
        }
        reader.close();
        return fileData.toString();
    }

    public static void saveStringAsFile(String filePath, String contents) {
        try {
            BufferedWriter out = new BufferedWriter(new FileWriter(filePath));
            out.write(contents);
            out.close();

        } catch (IOException ex) {
            logger.log(Level.SEVERE, "Error saving string as file", ex);
        }
    }

    public static boolean copyFile(String filePath, String targetDirectory) {
        File file = new File(filePath);
        String fileName = file.getName();
        try {
            Runtime.getRuntime().exec("cp " + filePath + " " + targetDirectory + "/" + fileName);
        } catch (IOException ex) {
            logger.log(Level.SEVERE, "Error copying file from " + filePath + " to " + targetDirectory, ex);
            return false;
        }
        return true;
    }

    public static String prepareRunDir(String runName) {
        String fullRunDirectory = runDirectory + '/' + runName;
        File dirFile = new File(fullRunDirectory);
        if (!dirFile.exists()) {
            dirFile.mkdir();;
        }
        return fullRunDirectory;
    }

    public static boolean removeDir(String dirPath) {
        logger.info("Removing run directory: " + dirPath);
        try {
            Runtime.getRuntime().exec("rm -rf " + dirPath);
        } catch (IOException ex) {
            logger.log(Level.SEVERE, "Error removing directory: " + dirPath, ex);
            return false;
        }
        return true;
    }

    public static String getRunDir(){
        return runDirectory;
    }

    public static String getScriptsDir(){
        return scriptsDirectory;
    }
}
