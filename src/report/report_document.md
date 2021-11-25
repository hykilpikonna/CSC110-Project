
# Meta Analysis

This section aims at gaining some insights about our data.

Our data come from three samples:
* `500-pop`: The list of 500 most followed users on Twitter.
* `500-rand`: A sample of 500 random users on Twitter who speaks English, Chinese, or Japanese with at least 1000 posts and at least 150 followers.
* `eng-news`: [Top 100 most influential news Twitter accounts by Nur Bremmen](https://memeburn.com/2010/09/the-100-most-influential-news-media-twitter-accounts/), combined with all news accounts which TwitterNews reposted.

## COVID-19 Posting Frequency

First, we analyzed how frequently the users in these three datasets are posing about COVID-19. Initially, we were expecting that most people will post about COVID-19 because this pandemic is very relevant to every one of us. However, we found that there are many people in our samples didn't post about COVID-19 at all. The following table shows how many people in each sample didn't post or posted less than 1% about COVID-19:

@include `/freq/didnt-post.md`

The `eng-news` sample has the lowest number of users who didn't have COVID-related posts, the `500-rand` sample has the highest, while `500-pop` sits in between. This large difference between `eng-news` and the rest can be explained by the news channels' obligation to report news, which includes news about new outbreaks, progress of vaccination, new cross-border policies, etc. Also, we observed that `500-pop` has much more users who posted COVID-related content than `500-rand`, while they have similar amounts of users posting less than 1%. This finding might be explained by how influential people have more incentive to express their support toward slowing the spread of the pandemic than regular users, which doesn't require frequent posting like news channels.

We might graph the frequencies on a histogram to gain more insight: (You can click on the images to enlarge them, and hold down E to view full screen).

<div class="image-row">
    <div><img src="/freq/500-pop-hist-outliers.png" alt="hist"></div>
    <div><img src="/freq/500-rand-hist-outliers.png" alt="hist"></div>
    <div><img src="/freq/eng-news-hist-outliers.png" alt="hist"></div>
</div>

However, as you can see, the graphs are not very helpful because the majority of the sample post below 0.1%, and there are many outliers who post very frequently, like 40%. For example, if we sort the samples by their frequency, we have a few outliers who post more than 20% even in the random sample:

@include-cut `/freq/500-rand-top-20.md` 0 10

## COVID-19 Popularity Ratios

To prevent division by zero, we ignored people who didn't post about COVID or didn't post at all.

Test Include:

@include `/pop/stats.md`

@include `/pop/ignored.md`

@include `/pop/stats-with-outliers.md`
