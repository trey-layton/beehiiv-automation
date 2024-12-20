instructions = {
    "content_generation": """
        First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `Paid recommendations are the easiest way to monetize subscribers instantly. Luckily, there are 3 simple ways to set them up. Today's newsletter breaks these down step-by-step to help you take advantage.` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc).
                All tweets should have a single "main_tweet" and a single "reply_tweet"
                For this reply tweet, this is only a single post, not a thread or anything, so don't use language suggesting otherwise. Also, the link is to subscribe as the newsletter has not gone out yet.
               Return the post in this EXACT format:
        
        ~!{"content_type": "postcta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here"},
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, check out the full article online now! {web_url}"}
                ]
        }!~ """,
    "image_relevance": """        
        ~!{"content_type": "postcta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, omit if no images},
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, check out the full article online now! {web_url}"}
                ]
        }!~ 
        """,
    "content_personalization": """
        For personalizing post-CTA tweets:
        1. Maintain the tweet's 280-character limit.
        2. Adapt the language to match the user's typical tweet style, including any recurring phrases or hashtags they use.
        3. Adjust the tone to match the user's usual level of formality or casualness.
        4. If the user tends to use certain types of hooks or openers, incorporate a similar style.
        5. Mimic the user's typical sentence structure and punctuation habits.
        6. If the user frequently uses certain emojis, consider incorporating them in a natural way.
        7. Ensure the personalized content still maintains the original tweet's purpose of teasing the newsletter content.
        Most importantly:
        - Do not change the structure or format of the content.
        - The edited content must be returned in exactly the same JSON format as it was provided.

        Return the edited post in this EXACT format:

        ~!{"content_type": "postcta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Do not change this line if present},
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, check out the full article online now! {web_url}"}
                ]
        }!~ 

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
    "hook_writing": """
        Return the edited post in this EXACT format:

        ~!{"content_type": "postcta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Do not change this line if present},
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, check out the full article online now! {web_url}"}
                ]
        }!~  

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
    "ai_polish": """
        Return the edited post in this EXACT format:

        ~!{"content_type": "postcta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Do not change this line if present},
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, check out the full article online now! {web_url}"}
                ]
        }!~ 

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
}
