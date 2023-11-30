package com.vincenzogulisano.util;
import org.github.jamm.MemoryMeter;

import com.vincenzogulisano.usecases.linearroad.TupleInput;
import com.vincenzogulisano.usecases.linearroad.WindowCountStops;

public class LinkedListOverheadTest {

    public static void main(String[] args) {
        

        // long totalMemory = Runtime.getRuntime().totalMemory();
        // long freeMemoryBefore = Runtime.getRuntime().freeMemory();
        
      for (int i = 0; i < 100; i++) {
        
        WindowCountStops w = new WindowCountStops();
        w.setInstanceNumber(0);
        w.setKey("ABCD");
        w.setLatestStimulus(0);
        w.setParallelismDegree(0);
        w.slideTo(0);
        int tuples = 0;
        for (int j = 0; j < i; j++) {
          tuples++;
          w.add(TupleInput.fromReading("0,86400,120,10,0,0,1,37,200639") );
        } 

        // long freeMemoryAfter = Runtime.getRuntime().freeMemory();
        // long usedMemory = freeMemoryBefore - freeMemoryAfter;
        // System.out.println("usedMemory: " + usedMemory);
        // System.out.println("estimated usedmemory: " + w.getSizeInBytes());

        // Create an instance of the MemoryMeter class
        MemoryMeter meter = new MemoryMeter();
        // Get the deep size of the object in bytes
        long size = meter.measureDeep(w);

        // Print the size in bytes
        // System.out.println("Object size: " + size + " bytes");
        System.out.println(tuples+","+w.getSizeInBytes()+","+size);

      }

    }
}