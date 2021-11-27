
# TODO: TITLE

## Introduction

We have observed that there have been increasingly more voices talking about COVID-19 since the start of the pandemic. However, different groups of people might view the importance of discussing the pandemic differently. For example, we don't know whether the most popular people on Twitter will be more or less inclined to post COVID-related content than the average Twitter user. Also, while some audience finds these content interesting, others quickly scroll through them. **So, we aim to compare people's interests in posting coronavirus content and the audience's interests in viewing them between different groups.** Also, with recent developments and policy changes toward COVID-19, it is unclear how people's discussions would react. Some people might believe that the pandemic is starting to end so that discussing it would seem increasingly like an unnecessary effort, while others might find these policy changes controversial and want to voice their opinions even more. Also, even though COVID-related topics are almost always on the news, some news outlets might intentionally cover them more frequently than others. For the people watching the news, some people might find these news reports interesting, while others can't help but switch channels. So, how people's interest in listening or discussing COVID-related topics changes over time is not very clear. **Our second goal is to analyze how people's interest in COVID-related topics changes and how frequently people have discussed COVID-related issues in the two years since the pandemic started.**

# Method

Our data come from three samples:

* `500-pop`: The list of 500 most followed users on Twitter who post in English, Chinese, or Japanese.
* `500-rand`: A sample of 500 random users on Twitter who post in English, Chinese, or Japanese with at least 1000 posts and at least 150 followers.
* `eng-news`: A list of 100 top news Twitter accounts by Nur Bremmen [[1]](#ref1), combined with all news accounts which TwitterNews reposted. All of them post in English, and most of them target audience in North America.

We also counted the number of people speaking each language:

@include `/sample-demographics.md`

## Data Collection

1. To create our samples, we collected a wide range of Twitter users using Twitter's get friends list API endpoint [(documentation)](https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/follow-search-get-users/api-reference/get-friends-list) and the follows-chaining technique. We specified one single user as the starting point, obtained the user's friends list, then we picked 3 random users and 3 most followed users from the friend list, add them to the queue, and start the process again from each of them. Because of Twitter's rate limiting on the get friends list endpoint, we can only obtain a maximum of 200 users per minute, with many of them being duplicates. We ran the program for one day and obtained 224,619 users (852.3 MB decompressed). However, only the username, popularity, post count, and language data are kept after processing (filtering). The processed user dataset `data/twitter/user/processed/users.json` is 7.9 MB in total. We selected our samples by filtering the results first based on language, selected the top 500 most followed users as `500-pop`, filtered the list again based on post count (>1000) and followers (>150), then selected a random sample of 500 users as `500-rand`.

2. Tweets (ignoring retweets) **TODO**

## Computation

To analyze the frequencies and relative popularity of COVID-related posting either for all posts from a specific user, or for a sample across many users for a specific date, we defined several formulas. First, we need to define many terms we will use in the following sections:

* **Frequency**: The percentage of COVID-related posts compared to all posts, showing how frequent COVID-related content are posted.
* **Popularity**: The integer value representing the popularity of a post, measured by the total number of user interactions on a post, which is the number of likes and comments on a tweet combined.
* **Popularity Ratio**: The relative popularity between 0 and infinity calculating how popular are a user's COVID-posts compared to all the user's posts, which is a ratio of the average popularity of COVID-posts over all posts. If COVID-posts are more popular, then this value should be greater than 1, and if they are less popular, this value should be less than 1. Since follower count and interaction rate differs wildly between users, we cannot assume that popularity is comparable between users, so popularity is only compared within a user, while popularity ratio can be compared across users.

In the first section, we used the following formulas to calculate statistical distributions of the frequencies and popularity ratios of users in a sample:

<blockquote>
$$ \text{freq}_{u} = \frac{|\text{COVID-posts by } u|}{|\text{All posts by } u|} $$
</blockquote>

<blockquote>
$$ \text{pop_ratio}_{u} = \left(\frac{\sum\text{Popularity of COVID-posts by } u}{|\text{COVID-posts by } u|}\right) / \left(\frac{\sum \text{Popularity of all posts by } u}{|\text{All posts by } u|}\right) $$
</blockquote>

In the second section, we used the following formulas to calculate frequencies and popularity ratios for each date across many users in one sample:

**TODO**

# Meta Analysis

This section ignores date and focuses on user differences within our samples, which will answer the first part of our research question: **how frequently does people post about COVID-related issues, and how interested are people to see COVID-related posts?**

## Method & Results - COVID-19 Posting Frequency

**TODO: Separate method from results**

First, we analyzed how frequently the users in these three datasets are posing about COVID-19 (ignoring retweets). Initially, we were expecting that most people will post about COVID-19 because this pandemic is very relevant to every one of us. However, we found that there are many people in our samples didn't post about COVID-19 at all. The following table shows how many people in each sample didn't post or posted less than 1% about COVID-19:

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

So, we removed the outliers using the method proposed by Boris Iglewicz and David Hoaglin (1993) [[2]](#ref2) and ignoring everyone who posted below 0.1% and graphed the same histogram again:

<div class="image-row">
    <div><img src="/freq/500-pop-hist.png" alt="hist"></div>
    <div><img src="/freq/500-rand-hist.png" alt="hist"></div>
    <div><img src="/freq/eng-news-hist.png" alt="hist"></div>
</div>

As expected, the distributions looks right-skewed, with most people posting not very much. One interesting distinction is that, even though the distributions follow similar shapes, the x-axis ticks of `eng-news` is actually ten times larger than the other two, which means that `eng-news` post a lot more about COVID-19 on average than the other two samples. We can calculate some statistics of the samples to further verify this:

@include-lines `/freq/stats.md` 0 1 4 5

Since there are many outliers, medians and IQR will more accurately represent the center and spread of this distribution. As these numbers show, `eng-news` do post much more (a 6.1% increment in post frequency, or a 406.7% increase) than the other two samples. Again, this can be explained by the news channels' obligation to report news related to COVID-19 or to promote methods to slow the spread of the pandemic.

## Results - COVID-19 Popularity Ratios

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

The second section analyzes data separate for each of our samples, just like the previous analysis. However, unlike how calculations are separated for each user in the first section, the second section separates calculation by date and combines users in a sample. We defined the start of COVID-19 as _2020-01-01_ and ignored all posts prior to this date. Then, we calculate the average frequency and popularity ratio for every day since _2020-01-01_. This calculation gave us a list `freqs` and a list `pops` where, for every date `dates[i]`,

<blockquote>
$$ \text{freqs}_i = \frac{|\text{COVID-posts on date}_{i}|}{|\text{All posts on date}_{i}|} $$
</blockquote>

<blockquote>
$$ \text{pops}_i = \frac{ \sum_{u \in \text{Users}} \left(\frac{\sum\text{Popularity of u's COVID-posts on date}_i}{(\text{Average popularity of all u's posts}) \cdot |\text{u's COVID-posts on date}_i|}\right)}{(\text{Number of users posted on date}_i)} $$
</blockquote>

After calculation, we decided to plot line charts of `freqs` or `pops` against `dates`. Initially, we are seeing graphs with very high peaks such as the graph below. After some investigation, we found that these peaks are caused by not having enough tweets on each day to average out the random error of one single popular tweet. For example, in the graph below, we adjusted the program to print different users' popularity ratios when we found an average popularity ratio of greater than 20, which produced the output on the right. As it turns out, on 2020-07-11, the user @juniorbachchan posted that he and his father tested positive, and that single post is 163.84 times more popular than the average of all his posts. (The post is linked [here](https://twitter.com/juniorbachchan/status/1282018653215395840), it has 235k likes, 25k comments, and 32k retweets). Even though these data points are outliers, there isn't an effective way of removing them since we don't have enough tweets data from each user to calculate their range (for example, someone's COVID-related post might be the only one they've posted). So, we've decided to limit the viewing window to `y = [0, 2]` as shown in the graph on the right.

<div class="image-row">
    <div><img src="resources/peak-1.png" alt="graph"></div>
    <div style="display: flex; flex-direction: column; justify-content: center"><pre>
Date:  2020-07-11
- JoeBiden 1.36
<span class="highlight">- juniorbachchan 163.84</span>
- victoriabeckham 0.80
- anandmahindra 7.66
- gucci 0.13
- StephenKing 0.61
    </pre></div>
    <div><img src="resources/peak-2.png" alt="graph"></div>
</div>

Then, we encountered the issue of noise. When we plot the graph without a filter, we found that the graph is actually very noisy. We decided to average the results over 7 days. Then, we also experimented with different filters from the `scipy` library and different parameter values, and chose to use an IIR filter with `n = 10`.

<div class="image-row">
    <div><img src="/change/n/5.png" alt="graph"></div>
    <div><img src="/change/n/10.png" alt="graph"></div>
    <div><img src="/change/n/15.png" alt="graph"></div>
</div>

## Results - Posting Frequency Over Time

We graphed the posting frequencies of our three samples in line graphs with the x-axis being the date with labels representing the month, which gave us the following graphs:

<div class="image-row">
    <div><img src="/change/freq/500-pop.png" alt="graph"></div>
    <div><img src="/change/freq/500-rand.png" alt="graph"></div>
    <div><img src="/change/freq/eng-news.png" alt="graph"></div>
</div>

Looking at three graphs individually, the posting rates were almost zero during the first two month when COVID-19 first started for all three samples, which is expected because no one knew how devastating it will be at that time. Then, all three samples had a peak in posting frequencies from March to June 2020. After June 2020, the posting rate for both `500-rand` and `eng-news` declined to around 1/3 of the peak, with `500-pop` declining slightly as well. While the reason to this decline is unclear, we speculate that it might be caused by people's loss of interest in the topic as they realize COVID-19 isn't going to be a disaster that fades away quickly, or as the news became less "breaking" and information started to repeat. Like the selective attention theory of cognitive psychology, people's attention to one thing comes at the expense of others since our attention is very limited. So people might have chosen to direct more attention to living rather than paying attention to the coronavirus that didn't seem to go away soon. Also, similar to how people will unconsciously learn to ignore repeated background noise after moving to a new environment (in a process called habituation), they might have learned to ignore the repeated information about COVID-19, which will lead to less COVID-related posting. Further research can determine whether this three-month attention span can generalize to other long-term disaster other than COVID-19.

After June 2020, `500-rand` continued declining steadily without major peaks, while `eng-news` had a smaller peak around Dec 2020 and a trough after June 2021, and `500-top` had many peaks and toughs after. In an effort to interpret these peaks, we overlapped the three charts with the data of new COVID-19 cases in the U.S. published by New York Times [[3]](#ref3), which gave us the following graph: 

<div class="image-row">
    <div><img src="/change/comb/freq.png" alt="graph" class="large"></div>
</div>

In this graph, we can see that the peak around Dec 2020 and the trough around Jun 2021 in `eng-news` and `500-pop` actually correspond very closely with the rise and fall of new cases in the U.S., which is reasonable because there are more sensational news to report and more COVID-related events happening to popular individuals when cases are high. However, even though the first peak in cases around August 2020 did correlate with a peak in `500-rand`, the rise and fall of cases in the U.S. doesn't seem to affect `500-rand` overall. This is possibly because we included three languages in the population of our random sample, which means that `500-rand` isn't limited to English-speaking accounts that mostly target the U.S. audience like `eng-news`.

## Results - Popularity Ratio Over Time

We graphed a similar graph with popularity ratio being the y-axis over date as the x-axis, as shown below:

<div class="image-row">
    <div><img src="/change/comb/pop.png" alt="graph" class="large"></div>
</div>

Despite efforts to filter out noise or normalize the graph discussed in the [method](#method) section, we did not find any patterns in the resulting graph. The peaks and troughs of each line seems random, and the three lines did not have common peaks or troughs that might reveal meaningful insights. The raw data looks very much like random noise as well. This lack of meaningful information is possibly because our sample size is comparatively small—even though we have 500 users in our `500-pop` sample, the sample size for tweets by these users on one specific day is very small. For example, there are only 6 users in `500-pop` who posted on `2020-07-11`. This lack of samples amplified the effect of randomness, and more data may be needed to reduce the effect of one tweet on the popularity ratio for the specified date. Unfortunately, we have to reach a conclusion that more data is needed to reveal interesting findings.

# Conclusion

_**TODO**_: A conclusion

* Why are these findings important? What do they reveal?
* Connect to larger theme?

## Scratch pad (TODO)

For the posting frequency, it is surprising that all three of our samples have posting frequencies dropped significantly after June 2020, as if everyone silently agreed to talk less about it.

Possible reasons:

* There might not be as many "breaking news" or new information anymore, as three months is probably enough that everyone are aware of the virus.
* People realized that COVID-19 is not going to be a disaster that fade away quickly and got used to it, so people paid less attention because our attention is very limited. (**TODO**: Possible psychological explanation? -- Look into how long people have paid attention to an unexpected disaster on average. Compare attention with historical disasters like 911?)
* ~~Chinese people might be relieved because new daily cases are already controlled to two digits since April.~~ (Doesn't explain why `eng-news` declined)
* ~~Reopening in China around June.~~ (Doesn't explain why `eng-news` declined)
* ~~The first time cases seem to decline in U.S.~~ (Cases went back to increasing one month later but the posting frequency didn't go back up.)

**_TODO_**

* [ ] Frequency/time: Maybe there's a reason to the May 2021 peak?
* [ ] Followers (x) vs COVID-related posts (y) scatter plot, each point is a user

## References

<a id="ref1"></a>

[1] Bremmen, N. (2010, September 3). The 100 most influential news media twitter accounts. _Memeburn_. Retrieved November 27, 2021, from https://memeburn.com/2010/09/the-100-most-influential-news-media-twitter-accounts/.

<a id="ref2"></a>

[2] Iglewicz, Boris, & David Hoaglin (1993), "Volume 16: How to Detect and
Handle Outliers", _The ASQC Basic References in Quality Control:
Statistical Techniques_, Edward F. Mykytka, Ph.D., Editor.

<a id="ref3"></a>

[3] The New York Times. (2021). Coronavirus (Covid-19) Data in the United States. Retrieved November 27, 2021, from https://github.com/nytimes/covid-19-data.

<a id="ref4"></a>

[4] WHO. (n.d.) _Listings of WHO's Response to COVID-19._ World Health Organization. Retrieved November 27, 2021, from https://www.who.int/news/item/29-06-2020-covidtimeline.
