import java.util.*;

import static java.util.Collections.*;

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

public class RandomizerByDistribution<T> {
    public static class Share<T> {
        final T entity;
        final float share;

        public Share(T entity, float share) {
            this.entity = entity;
            this.share = share;
        }

        public String toString() {
            return "Share(" + entity + ":" + share + ")";
        }

        public static <T> float calcSum(List<Share<T>> distribution) {
            float sum = 0;
            for(Share<T> share : distribution)
                sum += share.share;
            return sum;
        }
    }

    final List<Share<T>> referenceDistribution;
    final float shareSummary;
    Random rnd = new Random(System.currentTimeMillis());

    Comparator<Share<T>> BIGGER_GOES_FIRST = new Comparator<Share<T>>() {
        public int compare(Share<T> o1, Share<T> o2) {
            if (o1.share < o2.share) return +1;
            else if (o1.share > o2.share) return -1;
            else return 0;
        }
    };

    public RandomizerByDistribution(List<Share<T>> referenceDistribution) {
        this.referenceDistribution = referenceDistribution;
        this.shareSummary = Share.calcSum(this.referenceDistribution);
        initOptimize();
    }

    private void initOptimize() {
        sort(this.referenceDistribution, BIGGER_GOES_FIRST);
    }

    public T next() {
        float srch = nextFloat();

        float left = 0F;
        for(Share<T> sh : referenceDistribution) {
            float right = left + sh.share;
            if(srch >= left && srch < right)
                return sh.entity;
            left += sh.share;
        }
        return referenceDistribution.get( referenceDistribution.size() - 1 ).entity;
    }

    /**
     * Get next random float from 0.0 to 1.0
     * Then normalize that value because shareSummary is not 1.0 exactly in real environment.
     */
    private float nextFloat() {
        return rnd.nextFloat() * shareSummary;
    }
}
