
# Meta Analysis

This section aims at gaining some insights about our data.

Our data come from three samples:
* `500-pop`: The list of 500 most followed users on Twitter.
* `500-rand`: A sample of 500 random users on Twitter who speaks English, Chinese, or Japanese with at least 1000 posts and at least 150 followers.
* `eng-news`: [Top 100 most influential news Twitter accounts by Nur Bremmen](https://memeburn.com/2010/09/the-100-most-influential-news-media-twitter-accounts/), combined with all news accounts which TwitterNews reposted.

## COVID-19 Posting Frequency

![](/1-covid-tweet-frequency/500-pop.png)

## COVID-19 Popularity Ratios

To prevent division by zero, we ignored people who didn't post about COVID or didn't post at all.

Test Include:

@include `/1-covid-tweet-frequency/500-pop.md`
