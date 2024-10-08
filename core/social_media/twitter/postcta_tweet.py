instructions = {
    "content_generation": """
        First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `Paid recommendations are the easiest way to monetize subscribers instantly. Luckily, there are 3 simple ways to set them up. Today's newsletter breaks these down step-by-step to help you take advantage.` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc).
                All tweets should have a single "main_tweet" and a single "reply_tweet"
                For this reply tweet, this is only a single post, not a thread or anything, so don't use language suggesting otherwise. Also, the link is to subscribe as the newsletter has not gone out yet.
               Return the post in this EXACT format:
        
            ["type": "postcta_tweet",
            "content": [
                {"type": "main_tweet", "content": "Main post content here"},
                {"type": "reply_tweet", "content": "If this sounds interesting, check out the full article online now! {web_url}"},
            ] """
}
