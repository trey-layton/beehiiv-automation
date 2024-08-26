import asyncio
import os
import time
from dotenv import load_dotenv
from PIL import Image
from core.models.account_profile import AccountProfile
from core.content.image_generator import (
    generate_image_list_content,
    generate_image_list,
)

load_dotenv()

# Include the newsletter content directly in the script
NEWSLETTER_CONTENT = """
Jenna Ortega Exposes the Dark Side of AI 😳
PLUS: Google in warfare, $1b AI boom in coding, and India’s Secret Weapon in the AI Race
AuthorAuthor
Ihtesham Haider & Hasan Toor
August 26, 2024

In partnership with



Welcome, Prohumans.

This issue uncovers some of the most controversial and groundbreaking AI developments to date.

From Google DeepMind employees pushing back against military contracts to AI-powered coding becoming a billion-dollar industry, we’ve got the stories you need to know.

And if you thought AI couldn’t get darker, wait until you read about Jenna Ortega’s shocking experience with AI-generated images.

In today’s post:

Google AI warfare

$1B AI Coding Surge

Jenna Ortega AI Scandal

India’s Voice Bots


Google AI revolt 🔫 

The growing unrest at Google DeepMind has surfaced, as over 100 employees penned an open letter urging Google to cease its military contracts, particularly with the Israeli military. They argue that such involvement directly conflicts with Google's AI Principles.

In short:

Over 100 employees signed the letter.

Focus on Google’s Project Nimbus with the Israeli military.

Concerns about AI being used for warfare and surveillance.

Employees demand an end to military contracts.

Google has yet to respond meaningfully.

Google faces a pivotal moment—will it adhere to its ethical guidelines, or continue down a path fraught with controversy?

Thoughts on this:

Google, Amazon, and other AI giants should remain neutral and doesn’t help any military whatsoever.

Because its new and we don’t if the it’s providing the military is correct if so then who is there to oversee.

What you think about this?

Let me know.

🧑‍💻 AI Coding Raises Nearly $1 Billion, Claiming ‘Killer App’ Status

The AI coding assistants are changing software engineering, pulling in close to $1 billion in funding since last year.

This surge signals the emergence of coding as the first “killer app” for generative AI.

In short:

Companies like Replit, Anysphere, and Magic are leading the charge.

$433 million raised this year alone, totaling $906 million since January 2023.

AI’s impact on coding is becoming indispensable in tech circles.

Giants like Microsoft and Amazon are competing fiercely in this space.

AI coding assistants are not just tools—they’re revolutionizing how software is built, marking the dawn of a new era in programming.

Jenna Ortega say no to AI explicit images and delete 𝕏/Twitter

Jenna Ortega, the young star, revealed that she deleted her Twitter account after encountering disturbing AI-generated explicit images of herself as a minor.

The details you need to know:

Ortega was 14 when she first saw edited explicit content.

The issue worsened after her role in "Wednesday" in 2022.

AI-generated deepfakes have targeted her and other celebrities.

Ortega’s experience highlights the darker side of AI technology.

The Dark Side of AI:

As AI tools advance, the line between innovation and violation blurs—Ortega’s story is a chilling reminder of the need for ethical boundaries.

I think we should regulate such softwares as quickly as possible.

What if they use our family members pictures to create such images and publish them online?

Penny-a-Minute Voice Bots Drive India’s AI Boom

India’s AI startups are leveraging voice technology to bridge the language divide, offering voice bots at just a rupee per minute.

This innovation could reshape how AI is used across the country.

The Details:

Sarvam AI launched a new voice bot product for businesses.

Bots are built using data from 10 native Indian languages.

Startups like Gnani AI and CoRover are tapping into diverse Indian markets.

Applications range from customer service to booking train tickets.

A Voice for the Future:

In a nation as diverse as India, voice bots are not just a technological advancement—they’re a key to unlocking AI’s full potential for all.

Read the stories in detail here:
Google AI warfare

$1B AI Coding Surge

Jenna Ortega AI Scandal

India’s Voice Bots

Together with PGA:
Writers making less than $5,000 per month:

Feeling underpaid and overworked?

Still charging per month (or worse, per hour)?

Tired of spinning on the freelancer hamster wheel?

Become a Premium Ghostwriter here.


Whenever you’re ready, there are 2 ways we can help you:

Help you promote your product and service to 150k+ engineers, AI enthusiasts, entrepreneurs, creators, and founders. Sponsor us

Help you build a irresistible brand on 𝕏/Twitter and LinkedIn in less than 6 months. We’ve helped 100+ creators from YouTube, entrepreneurs, founders, executives, and people like yourself. Contact us here: theprohumanai@gmail.com

Thanks for reading…
That’s a wrap.

typing typewriter GIF
What's on your mind?

Share your best ideas with us at theprohumanai@gmail.com.

We'll bring your ideas to life. Send them our way, and we'll get to work on making them a reality.

Did you find value in our newsletter today?
Your feedback can help us create better content for you!
❤️ Loved It!
😳 It was great!
😢 It was bad!
Login or Subscribe to participate in polls.



I hope this was useful…

If you want to learn more then visit this website.

Get your brand, product, or service in front of 150,000+ professionals here.

Follow us on 𝕏/Twitter to learn more about AI:

@hasantoxr & @ihteshamit
"""


async def generate_outreach_image(
    newsletter_content: str, output_dir: str = "outreach_images"
):
    # Create a dummy AccountProfile (since we don't need a real one for this tool)
    dummy_profile = AccountProfile(
        account_id="outreach_tool",
        beehiiv_api_key="",
        subscribe_url="",
        publication_id="",
        custom_prompt="",
    )

    # Generate content
    content = await generate_image_list_content(newsletter_content, dummy_profile)

    # Generate image
    image = generate_image_list(content, save_locally=False)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save the image
    timestamp = int(time.time())
    img_path = os.path.join(output_dir, f"outreach_image_{timestamp}.jpg")
    image.save(img_path, "JPEG")

    print(f"Image saved: {img_path}")
    print("Generated content:")
    print(content)

    return img_path, content


async def main():
    print("PostOnce Outreach Image Generator")
    print("Generating image from the included newsletter content...")

    img_path, content = await generate_outreach_image(NEWSLETTER_CONTENT)
    print(f"\nImage generated and saved to: {img_path}")
    print("You can now send this image to the newsletter creator.")


if __name__ == "__main__":
    asyncio.run(main())
