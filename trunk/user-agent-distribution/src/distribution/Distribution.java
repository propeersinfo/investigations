package distribution;

import java.util.HashMap;
import java.util.Map;

class Distribution<T> {
    private final Map<T,Float> map = new HashMap<T,Float>();
    private int totalCountOfUsages = 0;
    public void increment(T key) {
        Float value = map.get(key);
        if(value == null) {
            value = 0F;
        }
        map.put(key, value + 1F);
        totalCountOfUsages++;
    }

    public void debug() {
        for(T key : map.keySet()) {
            if(totalCountOfUsages == 0)
                System.err.println(key + " => " + map.get(key));
            else
                System.err.println(key + " => " + map.get(key) / totalCountOfUsages);
        }
    }
}
