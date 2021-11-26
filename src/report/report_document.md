
# Meta Analysis

This section aims at gaining some insights about the differences in our samples and the scode that the results might apply or generalize to. This section also answers the first part of our research question: **how frequently does people post about COVID-related issues, and how interested are people to see COVID-related posts?**

## Demographics

Our data come from three samples:
* `500-pop`: The list of 500 most followed users on Twitter.
* `500-rand`: A sample of 500 random users on Twitter who speaks English, Chinese, or Japanese with at least 1000 posts and at least 150 followers.
* `eng-news`: [Top 100 most influential news Twitter accounts by Nur Bremmen](https://memeburn.com/2010/09/the-100-most-influential-news-media-twitter-accounts/), combined with all news accounts which TwitterNews reposted.

## COVID-19 Posting Frequency

First, we analyzed how frequently the users in these three datasets are posing about COVID-19. Initially, we were expecting that most people will post about COVID-19 because this pandemic is very relevant to every one of us. However, we found that there are many people in our samples didn't post about COVID-19 at all. The following table shows how many people in each sample didn't post or posted less than 1% about COVID-19:

@include `/freq/didnt-post.md`

The `eng-news` sample has the lowest number of users who didn't have COVID-related posts, the `500-rand` sample has the highest, while `500-pop` sits in between. This large difference between `eng-news` and the rest can be explained by the news channels' obligation to report news, which includes news about new outbreaks, progress of vaccination, new cross-border policies, etc. Also, we observed that `500-pop` has much more users who posted COVID-related content than `500-rand`, while they have similar amounts of users posting less than 1%. This finding might be explained by how influential people have more incentive to express their support toward slowing the spread of the pandemic than regular users, which doesn't require frequent posting like news channels.

We calculated frequency by dividing the total number of tweets by the number of COVID-related tweets. We might graph the frequencies on a histogram to gain more insight: (You can click on the images to enlarge them, and hold down E to view full screen).

<div class="image-row">
    <div><img src="/freq/500-pop-hist-outliers.png" alt="hist"></div>
    <div><img src="/freq/500-rand-hist-outliers.png" alt="hist"></div>
    <div><img src="/freq/eng-news-hist-outliers.png" alt="hist"></div>
</div>

However, as you can see, the graphs are not very helpful because the majority of the sample post below 0.1%, and there are many outliers who post very frequently, like 40%. For example, if we sort the samples by their frequency, we have a few outliers who post more than 20% even in `500-rand`:

@include-cut `/freq/500-rand-top-20.md` 0 10

So, we removed the outliers using the method proposed by Boris Iglewicz and David Hoaglin (1993) [[1]](#ref1) and ignoring everyone who posted below 0.1% and graphed the same histogram again:

<div class="image-row">
    <div><img src="/freq/500-pop-hist.png" alt="hist"></div>
    <div><img src="/freq/500-rand-hist.png" alt="hist"></div>
    <div><img src="/freq/eng-news-hist.png" alt="hist"></div>
</div>

As expected, the distributions looks right-skewed, with most people posting not very much. One interesting distinction is that, even though the distributions follow similar shapes, the x-axis ticks of `eng-news` is actually ten times larger than the other two, which means that `eng-news` post a lot more about COVID-19 on average than the other two samples. We can calculate some statistics of the samples to further verify this:

@include-lines `/freq/stats.md` 0 1 4 5

Since there are many outliers, medians and IQR will more accurately represent the center and spread of this distribution. As these numbers show, `eng-news` do post much more (6.1% more post3, or a 1220% increase) than the other two samples. Again, this can be explained by the news channels' obligation to report news related to COVID-19 or to promote methods to slow the spread of the pandemic.

## COVID-19 Popularity Ratios

Then, we analyzed the popularity ratio of COVID-related posts for our three samples. The popularity of a post defines how much other people are interested in the post, measured by the total number of user interactions (likes and comments) on that post. From that data, the relative popularity ratio for COVID-related posts calculates how popular are COVID-related posts compared to all other posts, calculated by the equation, which is a ratio of the average popularity of both:

<blockquote>
$$ pop_{user} = \left(\frac{\sum\text{Popularity of COVID-posts}}{|\text{COVID-posts}|}\right) / \left(\frac{\sum \text{Popularity of all posts}}{|\text{All posts}|}\right)$$
</blockquote>

There are three divisions in this equation, so there are three possible places where it might divide by zero. So, to prevent division by zero, we ignored people who didn't post about COVID-19 or didn't post anything at all, and we also ignored people who have literally 0 popularity on any of their posts. In our data, we ignored this amount of people for each sample:

@include `/pop/ignored.md`

Graphing the results, we find that the ***TODO***

<div class="image-row">
    <div><img src="/pop/500-pop-hist.png" alt="hist"></div>
    <div><img src="/pop/500-rand-hist.png" alt="hist"></div>
    <div><img src="/pop/eng-news-hist.png" alt="hist"></div>
</div>

@include-lines `/pop/stats.md` 0 1 2 3 4 5


# Change Analysis

After we answered how frequently people posted about COVID-19 and how interested are people to view these posts, we analyze our data over the posting dates to answer the second part of our research question: **How does posting frequency and people's interests in COVID-19 posts changes from the beginning of the pandemic to now?**

## Method

This analysis is separate for each of our samples, just like the previous analysis. However, unlike how tweets are separated for each user in the previous analysis, we combine the tweets of all users in each sample in this analysis. In this analysis, we defined the start of COVID-19 as _2020-01-01_ and ignored all posts prior to this date. Then, we calculate the average frequency and popularity ratio for every day since _2020-01-01_. This calculation gave us a list `freqs` and a list `pops` where, for every date `dates[i]`,

<blockquote>
$$ \text{freqs}_i = \frac{|\text{COVID-posts on date}_{i}|}{|\text{All posts on date}_{i}|} $$
</blockquote>

<blockquote>
$$ \text{pops}_i = \left(\frac{\sum\text{Popularity of COVID-posts on date}_i}{|\text{COVID-posts on date}_i|}\right) / \left(\frac{\sum \text{Popularity of all posts on date}_i}{|\text{All posts on date}_i|}\right) $$
</blockquote>

After calculation, we decided to plot line charts of `freqs` or `pops` against `dates`. When we plot the graph without a filter, we found that the graph is actually very noisy as shown in the first graph below. So, we experimented with different filters from the `scipy` library and different parameter values, and chose to use an IIR filter with `n = 10`.

<div class="image-row">
    <div><img src="/change/n/1.png" alt="hist"></div>
    <div><img src="/change/n/4.png" alt="hist"></div>
    <div><img src="/change/n/10.png" alt="hist"></div>
</div>


**_TODO_**

## References

<a id="ref1"></a>

[1] Iglewicz, Boris, & David Hoaglin (1993), "Volume 16: How to Detect and
Handle Outliers", _The ASQC Basic References in Quality Control:
Statistical Techniques_, Edward F. Mykytka, Ph.D., Editor.

