package com.vincenzogulisano.util;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

import org.apache.commons.cli.*;

public class OutputComparator {
    
    public static void main(String[] args) {
        Options options = new Options();
        options.addOption("f1", "file1", true, "input file 1 path");
        options.addOption("f2", "file2", true, "input file 2 path");

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine cmd = parser.parse(options, args);
            String file1Path = cmd.getOptionValue("f1");
            String file2Path = cmd.getOptionValue("f2");
            compareTimestamps(file1Path, file2Path);
        } catch (ParseException e) {
            System.err.println("Error: " + e.getMessage());
            HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp("TimestampComparator", options);
        }
    }

    private static void compareTimestamps(String file1Path, String file2Path) {
        Map<Long, Set<String>> timestamps1 = new TreeMap<>();
        Map<Long, Set<String>> timestamps2 = new TreeMap<>();
        try {
            readAndSaveFileTimestamps(file1Path, timestamps1);
            readAndSaveFileTimestamps(file2Path, timestamps2);
        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            return;
        }
        System.out.println("Timestamps found in file 1: " + timestamps1.size());
        System.out.println("Timestamps found in file 2: " + timestamps2.size());

        Set<Long> sharedTimestamps = new TreeSet<>(timestamps1.keySet());
        sharedTimestamps.retainAll(timestamps2.keySet());

        System.out.println("Shared timestamps: " + sharedTimestamps.size());
        for (long timestamp : sharedTimestamps) {
            Set<String> lines1 = timestamps1.get(timestamp);
            Set<String> lines2 = timestamps2.get(timestamp);
            if (lines1.equals(lines2)) {
                System.out.println("Timestamp " + timestamp + " is the same in both files.");
            } else {
                System.out.println("Timestamp " + timestamp + " is different in both files.");
                // System.out.println("Lines in file 1:");
                // for (String line : lines1) {
                //     System.out.println(line);
                // }
                // System.out.println("Lines in file 2:");
                // for (String line : lines2) {
                //     System.out.println(line);
                // }
            }
        }

        Set<Long> timestampsOnlyInFile1 = new TreeSet<>(timestamps1.keySet());
        timestampsOnlyInFile1.removeAll(timestamps2.keySet());
        System.out.println("Timestamps only in file 1: " + timestampsOnlyInFile1.size());
        for (long timestamp : timestampsOnlyInFile1) {
            int index = getTimestampIndex(timestamps1, timestamp);
            System.out.println("Timestamp " + timestamp + " is only in file 1, at index " + index);
        }

        Set<Long> timestampsOnlyInFile2 = new TreeSet<>(timestamps2.keySet());
        timestampsOnlyInFile2.removeAll(timestamps1.keySet());
        System.out.println("Timestamps only in file 2: " + timestampsOnlyInFile2.size());
        for (long timestamp : timestampsOnlyInFile2) {
            int index = getTimestampIndex(timestamps2, timestamp);
            System.out.println("Timestamp " + timestamp + " is only in file 2, at index " + index);
        }
    }

    private static void readAndSaveFileTimestamps(String filePath, Map<Long, Set<String>> timestamps) throws IOException {
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] tokens = line.split(",");
                long timestamp = Long.parseLong(tokens[0]);
                Set<String> lines = timestamps.getOrDefault(timestamp, new HashSet<>());
                lines.add(line);
                timestamps.put(timestamp, lines);
            }
        }
    }
    
    private static int getTimestampIndex(Map<Long, Set<String>> timestamps, long timestamp) {
        int index = 0;
        for (long key : timestamps.keySet()) {
            if (key < timestamp) {
                index++;
            } else if (key == timestamp) {
                return index;
            } else {
                break;
            }
        }
        return -1; // not found
    }

}