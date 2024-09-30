import re
from core.content.language_model_client import call_language_model
from core.models.account_profile import AccountProfile


async def generate_linkedin_post(text: str, account_profile: AccountProfile) -> str:
    try:
        # Use custom prompt if available, otherwise use the default example
        example_post = """
How to build a holding company (without millions $$$): 
 
Everyone thinks you need millions of dollars to build a holding company. 
 
At least I did. 
 
Then I built one & realized it's simpler than you think. 
 
Here are the basics: 
 
Building a portfolio of businesses isn't about having millions. 
 
It's about two things: 
• Scale 
• Leverage 
 
Let's break it down: 
 
1. Scale 
 
Start where you are, with what you've got. 
 
Like my pal Ramon. He was an ex-MMA fighter, single dad. His first biz cost $500. About 9yrs later, he says he bought one making 8 figures. 
 
How? Stairstepping. 
 
Stairstepping is like real estate: 
 
First you buy a studio → then a 1 bedroom → Townhouse → House → Multi-family → Industrial 
 
Same in business. 
 
You buy what you can. But you don't bankrupt yourself as you’re learning the game. 
 
Then here's the magic: 
 
When you're just starting, people actually WANT to help. So, what can you do? 
• Find people you want to model your baby berkshire after 
• Ask them direct questions. 
 
Congrats. Free board of directors. 
 
Next: 
 
Set timelines. And more importantly – meet expectations. 
 
Your plan might look like: 
"Buy my 1st biz for <$10k in 6mos. Then use the cashflow to buy the 2nd in 3mos." 
 
This is how you start a business flywheel. 
 
Now? Find where other owners & buyers are chilling. 
 
Hit up as many as humanly possible: 
• Send DMs 
• Attend events & conferences 
• Join communities (free first, paid later) 
 
When you surround yourself with owners, you multiply your odds of success. 
 
2. Leverage (aka Other People's Money) 
 
Two main things you need to understand: 
• SBA loans 
• Seller financing 
 
The fastest ways to get equity in things you can't afford with cash. 
 
Leverage is fun, if you can get creative. 
 
(We'll stay out of the weeds here, but you can take this guide on 6 ways to creatively finance. Download for later → https://lnkd.in/e9HaPZit) 
 
Now, once you get the ball rolling: 
 
Find your niches. Double down. 
 
If it works, keep doing it. 
 
Just bigger. 
 
When I first started buying biz's, I kept it simple with laundromats, carwashes, etc. 
 
Then I started buying businesses that helped expand my media company. 
 
Now, I'm making bigger bets, in the millions. And I'm making them publicly. 
 
One recent add to my portfolio: 
 
The home services franchise Resibrands (aka, those beautiful brands in this pic). Making blue collar work cool again & helping regular folks become owners. 
 
But that's not my only recent big bet... 
 
We're also working on something (BIG) that's going to make YOUR holding company easier to build. 
 
Buy your dream & build back Main Street..

Be the first to get more details about this (BIG) new project here → https://lnkd.in/eHwd3tXr
        """
        system_message = {
            "role": "system",
            "content": "You are a skilled content creator specializing in LinkedIn posts. Generate a post of approximately 1000 characters that summarizes the main points of the given content. The post should be informative, engaging, and have a 'thought leadership' tone. Do not use emojis. If the example post provided breaks these guidelines, override them with the example post instead as this was chosen specifically for the person. Each sentence or key point should be on a new line, separated by <br>. The post should be ready to publish on LinkedIn. Do not include any additional text, formatting, or placeholders beyond the <br> separators.",
        }
        user_message = {
            "role": "user",
            "content": f"Create a LinkedIn post summarizing this newsletter content. Use a professional style similar to this example, but adapted for LinkedIn: {example_post}\n\nHere's the newsletter content:\n{text}.  The first piece of content that I provided you was the example tweet. DO NOT WRITE ABOUT THE CONTENT OF IT. This example post is ONLY for structure replication, but the contents of the second piece of custom content you were provided are the actual newsletter contents, so write the post about the actual subject matter in this second piece of content.",
        }

        response_content = await call_language_model(
            system_message, user_message, tier="high"
        )

        # Extract post text from the response
        if isinstance(response_content, dict):
            post_text = (
                response_content.get("post") or response_content.get("text") or ""
            )
        elif isinstance(response_content, str):
            post_text = response_content
        else:
            print(f"Unexpected response format: {response_content}")
            raise ValueError("Invalid response format from language model API")

        # Clean up the post text
        post_text = post_text.strip().strip('"')
        post_text = post_text.replace("\n", "<br>")
        post_text = post_text.replace("<br><br>", "<br>")
        post_text = re.sub(r"^(Post:?\s*)", "", post_text, flags=re.IGNORECASE)

        print(f"Final LinkedIn post text (length {len(post_text)}):\n{post_text}")
        return post_text
    except Exception as e:
        print(f"Unexpected error in generate_linkedin_post: {str(e)}")
        raise
