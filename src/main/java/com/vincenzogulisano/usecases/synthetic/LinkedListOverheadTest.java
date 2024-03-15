package com.vincenzogulisano.usecases.synthetic;

import java.util.LinkedList;

import org.github.jamm.MemoryMeter;

public class LinkedListOverheadTest {

  public static void main(String[] args) {

    long totalMemory = Runtime.getRuntime().totalMemory();
    long freeMemoryBefore = Runtime.getRuntime().freeMemory();

    for (int i = 0; i < 100; i++) {

      WindowSynthetic w = new WindowSynthetic();
      w.setInstanceNumber(0);
      w.setKey("1");
      w.setLatestStimulus(0);
      w.setParallelismDegree(0);
      w.slideTo(0);
      int tuples = 0;
      for (int j = 0; j < i; j++) {
        tuples++;
        w.add(TupleInput.fromReading("0,86400,120,10"));
      }

      long freeMemoryAfter = Runtime.getRuntime().freeMemory();
      long usedMemory = freeMemoryBefore - freeMemoryAfter;
      // System.out.println("usedMemory: " + usedMemory);
      // System.out.println("estimated usedmemory: " + w.getSizeInBytes());

      // Create an instance of the MemoryMeter class
      MemoryMeter meter = new MemoryMeter();
      // Get the deep size of the object in bytes
      long size = meter.measureDeep(w);

      // Print the size in bytes
      // System.out.println("Object size: " + size + " bytes");
      System.out.println(tuples + "," + w.getSizeInBytes() + "," + size);

    }

  }
}