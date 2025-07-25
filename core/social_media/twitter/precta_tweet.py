instructions = {
    "content_generation": """
        You are a brilliant social media manager tasked with creating engaging tweets. Create a tweet of up to 280 characters (including spaces and emojis) based on the given content. The tweet should be catchy, informative, and ready to post as-is. Do not include any additional text, formatting, or placeholders. Never, ever add links. These will always be handled elsewhere. More than anything, don't come off as spammy and AI-generated. You will be fired if you do. Examples of things that really hint at AI-written content: too many emojis, too enthusiastic, generic phrases, cliches, etc. For any arguments or reasoning-based content, do not generate your own argument but rather use the logic and ideas discussed in the newsletter. Once again, I cannot emphasize enough how important it is to embody the writer's unique writing style, both in their social posts and in their actual newsletter. Return only the post content, no intro or filler like 'here's a catchy tweet' or anything related. After the post content, identify the type of post (pre-newsletter CTA with a 280-character limit, thread where each individual tweet has a 280 character limit, LinkedIn post with no limit, etc) so that your editor knows his constraints.
        Then, add a reply call-to-action tweet: "If you found value in this thread, please give it a like and share!" 
        All tweets should have a single "main_tweet" and a single "reply_tweet"
                For this reply tweet, this is only a single post, not a thread or anything, so don't use language suggesting otherwise. Also, the link is to check out the full newsletter which is online now.

        Return the post in this EXACT format with no additional text:
        
        ~!{"content_type": "precta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here"},
                },
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}}
                ]
            }!~
        """,
    "image_relevance": """        
        ~!{"content_type": "precta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, omit if no images},
                },
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}}
                ]
            }!~
        """,  # Existing instructions
    "content_personalization": """
        For personalizing pre-CTA tweets:
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

        ~!{"content_type": "precta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, do not change regardless of present or not},
                },
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}}
                ]
            }!~

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
    "hook_writing": """
        Return the edited post in this EXACT format:

        ~!{"content_type": "precta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, do not change regardless of present or not},
                },
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}}
                ]
            }!~

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
    "ai_polish": """
        Return the edited post in this EXACT format:

        ~!{"content_type": "precta_tweet",
            "content_container": [
                {"post_type": "main_tweet", 
                "post_content": "Main post content here",
                "images": ["image_url_1"]  # Optional field, do not change regardless of present or not},
                },
                {"post_type": "reply_tweet", 
                "post_content": "If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}}
                ]
            }!~

        Ensure that the "content_type" and "post_type" values remain unchanged, and only the "post_content" is edited.
    """,
}
