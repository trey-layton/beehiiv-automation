import logging
import json
import sys
from core.content.language_model_client import call_language_model
from core.models.account_profile import AccountProfile
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def format_tweet_with_link(tweet_text: str, link: str) -> str:
    # Remove any existing URLs from the tweet text
    tweet_text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        tweet_text,
    )

    # Trim any whitespace
    tweet_text = tweet_text.strip()

    # Ensure there's a space before the link
    if not tweet_text.endswith(" "):
        tweet_text += " "

    # Add the link
    tweet_text += link

    return tweet_text


async def generate_tweet(
    text: str, instruction: str, account_profile: AccountProfile
) -> str:
    logger.info(f"Generating tweet for account: {account_profile.account_id}")
    logger.info(f"Instruction: {instruction}")
    logger.info(f"Input text (first 100 chars): {text[:100]}...")
    system_message = {
        "role": "system",
        "content": "You are a brilliant social media manager tasked with creating engaging tweets. Create a tweet of up to 280 characters (including spaces and emojis) based on the given content. The tweet should be catchy, informative, and ready to post as-is. Do not include any additional text, formatting, or placeholders. Never, ever add links. These will always be handled elsewhere. More than anything, don't come off as spammy and AI-generated. You will be fired if you do. Examples of things that really hint at AI-written content: too many emojis, too enthusiastic, generic phrases, cliches, etc. For any arguments or reasoning-based content, do not generate your own argument but rather use the logic and ideas discussed in the newsletter. Once again, I cannot emphasize enough how important it is to embody the writer's unique writing style, both in their social posts and in their actual newsletter. Return only the post content, no intro or filler like 'here's a catchy tweet' or anything related. After the post content, identify the type of post (pre-newsletter CTA with a 280-character limit, thread where each individual tweet has a 280 character limit, LinkedIn post with no limit, etc) so that your editor knows his constraints.",
    }

    user_message = {
        "role": "user",
        "content": f"{instruction} Here's the newsletter content:\n{text}",
    }
    logger.info(f"System message: {system_message}")
    logger.info(f"User message: {user_message}")

    try:
        response_content = await call_language_model(system_message, user_message)
        logger.info(f"Raw LLM response: {response_content}")

        if isinstance(response_content, dict):
            tweet_text = (
                response_content.get("tweet") or response_content.get("text") or ""
            )
        elif isinstance(response_content, str):
            tweet_text = response_content
        else:
            raise ValueError("Invalid response format from language model API")

        return tweet_text.strip()
    except Exception as e:
        logger.exception(f"Unexpected error in generate_tweet: {str(e)}")
        raise


async def generate_precta_tweet(text: str, account_profile: AccountProfile) -> str:
    instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing pre-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `How to get newsletter subscribers -- for free. That's the topic of my newsletter tomorrow. I'm breaking down all the best ways to grow your email list organically without a large social following. Get access below:` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc)"
    main_tweet = await generate_tweet(text, instruction, account_profile)
    reply_tweet = f"If this sounds interesting, subscribe for free to get it in your inbox! {account_profile.subscribe_url}"
    return [
        {"type": "main_tweet", "text": main_tweet},
        {"type": "reply_tweet", "text": reply_tweet},
    ]


async def generate_postcta_tweet(
    text: str, account_profile: AccountProfile, web_url: str
) -> list:
    instruction = "First, go through this newsletter and isolate the main story. Then, turn the following newsletter into a super catchy, intriguing post-newsletter CTA TWEET (so never more than 280 characters) encouraging people on social media to read the newly published newsletter. Example: `Paid recommendations are the easiest way to monetize subscribers instantly. Luckily, there are 3 simple ways to set them up. Today's newsletter breaks these down step-by-step to help you take advantage.` but combine this content type with the writer's actual social media style (tone, syntax, punctuation, etc)."
    main_tweet = await generate_tweet(text, instruction, account_profile)
    reply_tweet = f"Check out the full thing online now! {web_url}"
    return [
        {"type": "main_tweet", "text": main_tweet},
        {"type": "reply_tweet", "text": reply_tweet},
    ]


async def generate_thread_tweet(
    text: str, article_link: str, account_profile: AccountProfile
) -> list:

    example_tweet = """tweet 1: "A professional sports gambler used analytics to turn a $700,000 loan into more than $300 million.

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
"""

    system_message = {
        "role": "system",
        "content": "You are a brilliant social media copywriter tasked with managing the social media accounts of the most brilliant, talented creators in the world. Generate a list of 5 tweets summarizing the main takeaways from the newsletter. Each tweet must be a maximum of 280 characters. Focus solely on one key point or insight, and don't include any other extra information. Return your answer as a JSON object with numbered keys (1., 2., 3., 4., 5.) for each tweet. Make sure each has a strong, punchy hook that keeps the reader engaged and motivated to move to the next tweet in the order. Make sure it sounds natural and make sure it flows well as a complete piece. only focus on the most important, big-picture lessons or takeaways from the newsletter. Return ONLY the document, no intro or conclusion text. More than anything, don't come off as spammy and AI-generated. You will be fired if you do. Examples of things that really hint at AI-written content: too many emojis, too enthusiastic, generic phrases, cliches, etc. For any arguments or reasoning-based content, do not generate your own argument but rather use the logic and ideas discussed in the newsletter. Once again, I cannot emphasize enough how important it is to embody the writer's unique writing style, both in their social posts and in their actual newsletter.",
    }

    user_message = {
        "role": "user",
        "content": f"Emulate the writer's actual social media style (tone, syntax, punctuation, etc) as seen in these examples classified by type of newsletter: '{example_tweet}'. Here's the newsletter content:{text}",
    }

    try:
        response_content = await call_language_model(system_message, user_message)
        print(f"\nRaw LLM response: {json.dumps(response_content, indent=2)}")

        tweets = []
        if isinstance(response_content, str):
            print("Response is a string, attempting to parse as JSON")
            try:
                json_str = re.search(r"\{.*\}", response_content, re.DOTALL)
                if json_str:
                    parsed_content = json.loads(json_str.group())
                    if isinstance(parsed_content, dict):
                        for key, tweet in parsed_content.items():
                            if key.rstrip(".").isdigit():
                                tweets.append(
                                    {"text": tweet.strip(), "type": "content"}
                                )
                                print(f"Added tweet: {tweet.strip()}")
                else:
                    print("No valid JSON found in the response")
            except json.JSONDecodeError:
                print("Failed to parse response as JSON")
                lines = response_content.split("\n")
                for line in lines:
                    if line.strip() and not line.strip().startswith(("{", "}")):
                        tweets.append({"text": line.strip(), "type": "content"})
                        print(f"Added tweet from line: {line.strip()}")
        elif isinstance(response_content, dict):
            print("Response is a dictionary")
            for key, tweet in response_content.items():
                if key.rstrip(".").isdigit():
                    tweets.append({"text": tweet.strip(), "type": "content"})
                    print(f"Added tweet: {tweet.strip()}")
        else:
            print(f"Unexpected response type: {type(response_content)}")

        # Add article link tweet
        tweets.append(
            {
                "text": f"If you want to go even deeper, check out the full article! {article_link}",
                "type": "article_link",
            }
        )

        # Add quote tweet
        tweets.append(
            {
                "text": "If you found value in this thread, please give it a like and share!",
                "type": "quote_tweet",
            }
        )

        print(f"\nGenerated {len(tweets)} tweets for the thread")
        print(f"Final tweets: {json.dumps(tweets, indent=2)}")
        return tweets
    except Exception as e:
        print(f"\nError in generate_thread_tweet: {str(e)}")
        raise


async def generate_long_form_tweet(text: str, account_profile: AccountProfile) -> str:
    example_tweet = """There is a proven playbook to grow companies.

The best entrepreneurs have a series of plays they run to print money. What tools to use, agencies to hire, strategies to employ.

Here is the exact 12 step strategy I've used to grow 3+ companies to millions in annual profit:

#1 - New logo with 99 designs. It costs $299 and is good enough for me.

#2 - New website by http://webrun.com. They've built 5 of my websites.

Whoever you chose, make sure it is SEO optimized and has landing pages for each of your services and each location.

KEEP IT SIMPLE.

A person who knows nothing about your business should be able to become your customer in 5 minutes or less.

#3 - Overseas talent hired through http://supportshepherd.com.

$5 an hour can get you an excellent back office employee. Game changer.

80% of my employees at a SELF STORAGE company are overseas. From management to financial underwriting to customer service.

You would be surprised how much can be managed and done from afar.

#4 - A Google Business profile you check and post on every single day. And you get all of your customers to write you a review.

This is a game changer as well and low hanging fruit.

#5 - Google ads running with http://adrhino.com.

Make sure you hire a company that can setup Google Analytics 4 and  track how the ads convert to customers.

You should get an ad spend amount per customer acquired so you can track profitability.

#6 - Link building plan to increase domain authority and Google ranking with http://boldseo.com.

The website structured correctly, content and these links are what will work for you.

Make sure to do "citations" as well with your name, address, phone number that list your company on all the directory sites like Yelp, Angies list, Yellow pages and more.

#7 - Make sure to get a premium .com domain for a few thousand bucks with less than 13 characters.

English words. Not .co. Not .net. Not .io.

People invest thousands into their business but make due with a $19 domain wit hyphens. Makes no sense.

#8 - Online banking with relayFi or Mercury. It is easy to send money and get cards for all your employees.

Don't accept cash or check. It is a waste of time and money. And people will steal it.

#9 - An online software to run your business. Jobber or another one like it.

A customer should be able to log in and pay an invoice in 2 minutes.

And you should be able to send them a professional invoice and take auto-payment for services.

#10 - Payroll tools like Deel (international) and Gusto make it super easy to run payroll.

#11 - Bookkeeping and tax returns through http://BetterBookkeeping.com.

I use them and they are awesome. Send monthly reports and prep tax returns.

#12 - Slack for communication. Loom for sharing training videos. Avoma for recording meetings. Notion for recording information and organizing data.

It's a cheat code to have these vendors to amplify my companies.

(I'm a partner in several of these companies - you don't need to use the exact ones I mention - just hire somebody good)

What do you have in your tech stack that I'm missing?

What tools do you love that I didn't share?

If you found this helpful - give me a retweet or a comment - it helps me spread the word!"""

    system_message = {
        "role": "system",
        "content": "You are a skilled social media ghost writer creating engaging long-form tweets for a top creator. Generate a tweet of approximately 850 characters that summarizes the main points of the given content. Each sentence should be on a new line, separated by <br>. The tweet should be informative, engaging, and ready to post manually. Do not include any additional text, formatting, or placeholders beyond the <br> separators. ONLY return the Tweet text, skipping any intro or conclusion text. Use a strong hook, but don't make it too clickbaity, and focus on the big picture. Make the post flow... you're telling the story, not making it choppy. More than anything, don't come off as spammy and AI-generated. You will be fired if you do. Examples of things that really hint at AI-written content: too many emojis, too enthusiastic, generic phrases, cliches, etc. For any arguments or reasoning-based content, do not generate your own argument but rather use the logic and ideas discussed in the newsletter. Once again, I cannot emphasize enough how important it is to embody the writer's unique writing style, both in their social posts and in their actual newsletter. The example tweet provided about the playbook to grow a business is for style. Do NOT use the content matter it provides in your output. If you catch yourself starting with 'growing a successful company requires a strategic approach and the right tools', stop and restart because you're talking about the example tweet and not the newsletter. At the end, separated from the post content, include the target length and tweet type so that your editor understands the context ",
    }

    user_message = {
        "role": "user",
        "content": f"Emulate the writer's actual social media style (tone, syntax, punctuation, etc) as seen in these examples classified by type of newsletter: '{example_tweet}'. Here's the newsletter content:{text}",
    }
    logger.info(f"System message: {system_message}")
    logger.info(f"User message: {user_message}")

    try:
        response_content = await call_language_model(system_message, user_message)
        logger.info(f"Raw LLM response: {response_content}")

        if isinstance(response_content, dict):
            tweet_text = (
                response_content.get("tweet") or response_content.get("text") or ""
            )
        elif isinstance(response_content, str):
            tweet_text = response_content
        else:
            raise ValueError("Invalid response format from language model API")

        logger.info(f"Generated long-form tweet: {tweet_text}")
        return tweet_text.strip()
    except Exception as e:
        logger.exception(f"Error in generate_long_form_tweet: {str(e)}")
        raise
