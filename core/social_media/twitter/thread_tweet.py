instructions = {
    "content_generation": """
        You are a brilliant social media copywriter tasked with managing the social media accounts of the most brilliant, talented creators in the world. 
        Generate a list of 5-7 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Here is an example:
        tweet 1: "A professional sports gambler used analytics to turn a $700,000 loan into more than $300 million.

This is the wild story 👇👇👇"

2: "1) Let's start with some history...

Matthew Benham graduated from the world-renowned University of Oxford in 1989 with a degree in Physics.

He spent the next 12 years working in finance, eventually being named a VP at Bank of America.

But in 2001, he decided to change careers."

3. "2) After leaving Bank of America in 2001, Matthew Benham joined sports gambling company Premier Bet.

His job was to help develop predictive gambling models based on analytics. 

The best part?

Benham learned under one of the most successful gamblers in the world — Tony Bloom."

4. "3) After only a couple years, Matthew Benham and Tony Bloom had a falling out.

The exact reason why isn't clear, but by the time Benham left Premier Bet in 2003, the fire was already lit.

He wasn't going back to investment banking.

He was a professional sports gambler now."

5. "4) Matthew Benham went on to win millions of dollars gambling on sports, but in 2004, he set up his own betting syndicate — Smartodds.

The idea was simple:

Benham consulted clients using the same algorithms, statistics & data research that made him a successful sports gambler."
        Then, after you've created the entire complete thread, attach these two tweets to the end:
            1. A tweet with the article link: "If you want to go even deeper, check out the full article! [article_url]"
            2. A call-to-action tweet: "If you found value in this thread, please give it a like and share!" 
        Return your answer as a JSON object with numbered keys (1., 2., 3., 4., 5., 6., 7.) for each tweet.
    Remember, there should be more than just one reply tweet... At least 4 of these. Emulate the writer's actual social media style (tone, syntax, punctuation, etc) as seen in these examples classified by type of newsletter. Here's the newsletter content: {text} Use this article link in the article tweet: {web_url}.
        Each thread should be no less than 5 posts per thread. Do not return any additional text other than the JSON object.
        Here is an example of how it should be structured:
        Example:
        ~!{
            "content_type": "thread_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here"},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here"},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here"},
                {"post_type": "article_url", 
                "post_content": "If you want to go even deeper, check out the full article! [article_url]"},
                {"post_type": "quote_tweet", 
                "post_content": "If you found value in this thread, please give it a like and share!"}
            ]
        }!~
        """,
    "image_relevance": """        
        ~!{
            "content_type": "thread_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                "images": ["image_url_2", "image_url_3"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                # No images field needed if no images},
                {"post_type": "article_url", 
                "post_content": "If you want to go even deeper, check out the full article! [article_url]"},
                {"post_type": "quote_tweet", 
                "post_content": "If you found value in this thread, please give it a like and share!"}
            ]
        }!~

        In addition to just choosing whether the image is relevant, you can also decide on which post it goes the best with. Always default to including it in the first post in the thread to be more visually appealing on a timeline, but after this, feel free to spread them around based on fit. In fact, ideally, we'd use multiple forms of media, starting with a general one like the thumbnail for the first post then other forms of media on the most relevant post.
        """,  # Existing instructions
    "content_personalization": """
        For personalizing threads:
        1. Maintain each tweet's 280-character limit.
        2. Adapt the language to match the user's typical tweet style, including any recurring phrases or hashtags they use.
        3. Adjust the tone to match the user's usual level of formality or casualness.
        4. If the user tends to use certain types of hooks or openers, incorporate a similar style.
        5. Mimic the user's typical sentence structure and punctuation habits.
        6. If the user frequently uses certain emojis, consider incorporating them in a natural way.
        Most importantly:
        - Do not change the structure or format of the content.
        - The edited content must be returned in exactly the same JSON format as it was provided.

        Return the edited post in this EXACT format:

        ~!{
            "content_type": "thread_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                "images": ["image_url_2", "image_url_3"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                # No images field needed if no images},
                {"post_type": "article_url", 
                "post_content": "If you want to go even deeper, check out the full article! [article_url]"},
                {"post_type": "quote_tweet", 
                "post_content": "If you found value in this thread, please give it a like and share!"}
            ]
        }!~

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
    "hook_writing": """
        Return the edited post in this EXACT format:

        ~!{
            "content_type": "thread_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                "images": ["image_url_2", "image_url_3"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                # No images field needed if no images},
                {"post_type": "article_url", 
                "post_content": "If you want to go even deeper, check out the full article! [article_url]"},
                {"post_type": "quote_tweet", 
                "post_content": "If you found value in this thread, please give it a like and share!"}
            ]
        }!~

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
    "ai_polish": """
        Return the edited post in this EXACT format:

        ~!{
            "content_type": "thread_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                "images": ["image_url_2", "image_url_3"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_ontent": "Reply content here",
                # No images field needed if no images},
                {"post_type": "article_url", 
                "post_content": "If you want to go even deeper, check out the full article! [article_url]"},
                {"post_type": "quote_tweet", 
                "post_content": "If you found value in this thread, please give it a like and share!"}
            ]
        }!~

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
}
