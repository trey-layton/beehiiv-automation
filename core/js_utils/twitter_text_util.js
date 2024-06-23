const twitter = require('twitter-text');

function validateTweetLength(tweet) {
    const result = twitter.parseTweet(tweet);
    return JSON.stringify({ valid: result.valid });
}

function autoLinkTweet(tweet) {
    return twitter.autoLink(tweet);
}

function extractEntities(tweet) {
    return JSON.stringify({
        mentions: twitter.extractMentions(tweet),
        hashtags: twitter.extractHashtags(tweet),
        urls: twitter.extractUrls(tweet)
    });
}

const [,, functionName, tweet] = process.argv;

if (functionName === 'validateTweetLength') {
    console.log(validateTweetLength(tweet));
} else if (functionName === 'autoLinkTweet') {
    console.log(autoLinkTweet(tweet));
} else if (functionName === 'extractEntities') {
    console.log(extractEntities(tweet));
}
