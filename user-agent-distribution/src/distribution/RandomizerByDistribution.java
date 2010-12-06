package distribution;

import java.util.*;

import static java.util.Collections.*;

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

    private final List<Share<T>> referenceDistribution;
    private final float shareSummary;
    private Random rnd = new Random(System.currentTimeMillis());

    private final Comparator<Share<T>> BIGGER_GOES_FIRST = new Comparator<Share<T>>() {
        public int compare(Share<T> o1, Share<T> o2) {
            return Float.valueOf(o1.share).compareTo(Float.valueOf(o2.share));
        }
    };

    public RandomizerByDistribution(List<Share<T>> referenceDistribution) {
        this.referenceDistribution = referenceDistribution;
        this.shareSummary = Share.calcSum(this.referenceDistribution);
        optimize();
    }

    private void optimize() {
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
