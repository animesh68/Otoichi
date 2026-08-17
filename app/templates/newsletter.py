from typing import Optional
from app.core.config import settings


def render_weekly_newsletter_html(
    artist_name: str,
    album_title: str,
    cover_art_url: Optional[str],
    description: Optional[str],
    format_name: str,
    vinyl_variant: str,
    price: float,
    stock_quantity: int,
    product_id: str,
    unsubscribe_token: str,
    audio_preview_url: Optional[str] = None,
    genre: Optional[str] = None,
    release_year: Optional[int] = None,
    subscriber_name: Optional[str] = None,
) -> str:
    """
    Render a responsive, editorial HTML email matching the Otoichi brand aesthetic.
    Concept: 'Letters from the Listening Room — One record worth hearing.'
    """
    app_url = settings.PUBLIC_APP_URL.rstrip("/")
    product_url = f"{app_url}/products/{product_id}"
    unsubscribe_url = f"{app_url}/newsletter/unsubscribe?token={unsubscribe_token}"
    greeting = f"Good morning, {subscriber_name.strip()}" if subscriber_name and subscriber_name.strip() else "Good morning"
    
    formatted_price = f"${price:.2f}"
    availability_text = "In Stock & Ready to Ship" if stock_quantity > 0 else "Limited / Archive Pressing"
    variant_display = vinyl_variant.replace("_", " ").title() if vinyl_variant else "Standard Black"
    meta_line = " • ".join(filter(None, [genre, str(release_year) if release_year else None, f"{format_name} ({variant_display})"]))

    cover_image_html = ""
    if cover_art_url:
        cover_image_html = f"""
        <div style="text-align: center; margin: 28px 0;">
            <a href="{product_url}" target="_blank" style="text-decoration: none;">
                <img src="{cover_art_url}" alt="{album_title} by {artist_name}" width="340" style="width: 100%; max-width: 340px; height: auto; border-radius: 6px; box-shadow: 0 16px 36px rgba(0,0,0,0.5); border: 1px solid #332B24; display: inline-block;" />
            </a>
        </div>
        """

    preview_button_html = ""
    if audio_preview_url:
        preview_button_html = f"""
        <div style="margin: 20px 0; text-align: center;">
            <a href="{product_url}" target="_blank" style="display: inline-block; padding: 10px 20px; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #C89B3C; background-color: rgba(200, 155, 60, 0.12); border: 1px solid #C89B3C; border-radius: 4px; text-decoration: none; font-weight: 500; letter-spacing: 0.05em;">
                &#9658; Listen to 30-Second Master Cut Preview
            </a>
        </div>
        """

    editorial_body = description or f"A singular master recording from {artist_name}, pressed with exceptional acoustic dynamic range. Dispatched in archival-grade inner sleeves."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letters from the Listening Room: {album_title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0E0C0A;
            color: #E6DFD5;
            font-family: Georgia, 'Times New Roman', serif;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #15120F;
            border: 1px solid #2B241E;
        }}
        .header {{
            background-color: #0A0807;
            padding: 36px 30px 24px;
            text-align: center;
            border-bottom: 1px solid #2B241E;
        }}
        .brand-title {{
            font-size: 26px;
            letter-spacing: 0.15em;
            color: #F5EFE6;
            margin: 0 0 6px 0;
            font-weight: 400;
        }}
        .brand-sub {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.22em;
            color: #C89B3C;
            margin: 0;
        }}
        .content {{
            padding: 36px 32px 40px;
        }}
        .salutation {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9E9182;
            margin-bottom: 20px;
        }}
        .concept-title {{
            font-size: 28px;
            line-height: 1.25;
            color: #F5EFE6;
            margin: 0 0 8px 0;
            font-weight: 400;
        }}
        .artist-name {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 15px;
            color: #C89B3C;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 0 16px 0;
            font-weight: 600;
        }}
        .meta-tag {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 12px;
            color: #7D7164;
            letter-spacing: 0.05em;
            margin-bottom: 20px;
        }}
        .description-text {{
            font-size: 16px;
            line-height: 1.7;
            color: #DDD4C7;
            margin: 24px 0 28px;
        }}
        .product-card {{
            background-color: #1C1814;
            border: 1px solid #332B24;
            border-radius: 6px;
            padding: 20px 24px;
            margin: 28px 0;
        }}
        .price-badge {{
            font-size: 22px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #F5EFE6;
            font-weight: 600;
        }}
        .cta-button {{
            display: block;
            background-color: #C89B3C;
            color: #0E0C0A;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-align: center;
            padding: 16px 28px;
            border-radius: 4px;
            text-decoration: none;
            margin: 28px 0 16px;
        }}
        .footer {{
            background-color: #0A0807;
            padding: 32px;
            text-align: center;
            border-top: 1px solid #2B241E;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11px;
            line-height: 1.6;
            color: #6E6357;
        }}
        .footer a {{
            color: #C89B3C;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div style="background-color: #0E0C0A; padding: 24px 12px;">
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1 class="brand-title">Otoichi <span style="color: #C89B3C;">音市</span></h1>
                <p class="brand-sub">Letters from the Listening Room &bull; Monday Issue</p>
            </div>

            <!-- Main Content -->
            <div class="content">
                <div class="salutation">{greeting},</div>
                <div style="font-family: Georgia, serif; font-style: italic; font-size: 15px; color: #C89B3C; margin-bottom: 8px;">
                    This week's selected pressing:
                </div>
                <h2 class="concept-title">{album_title}</h2>
                <div class="artist-name">{artist_name}</div>
                <div class="meta-tag">{meta_line}</div>

                {cover_image_html}

                {preview_button_html}

                <div class="description-text">
                    {editorial_body}
                </div>

                <!-- Product Snapshot Card -->
                <div class="product-card">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td align="left" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                                <div style="font-size: 11px; text-transform: uppercase; color: #8A7E72; letter-spacing: 0.08em;">Archival Format</div>
                                <div style="font-size: 14px; color: #F5EFE6; font-weight: 500; margin-top: 4px;">{format_name} ({variant_display})</div>
                            </td>
                            <td align="right" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                                <div class="price-badge">{formatted_price}</div>
                                <div style="font-size: 11px; color: #4ADE80; margin-top: 2px;">{availability_text}</div>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- CTA -->
                <a href="{product_url}" class="cta-button" target="_blank">
                    Inspect Pressing & Order &rarr;
                </a>
                <div style="text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; color: #6E6357;">
                    Inspected to Goldmine Grading standards &bull; Ships in custom heavy-duty mailers
                </div>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p style="margin: 0 0 10px 0;">
                    You are receiving this because you subscribed to <strong>Letters from the Listening Room</strong> on Otoichi.
                </p>
                <p style="margin: 0 0 10px 0;">
                    Dispatched weekly from the Kyoto & Tokyo archives.
                </p>
                <p style="margin: 0;">
                    <a href="{unsubscribe_url}">Unsubscribe in one click</a> &bull; <a href="{app_url}">Visit Storefront</a>
                </p>
            </div>
        </div>
    </div>
</body>
</html>"""


def render_weekly_newsletter_text(
    artist_name: str,
    album_title: str,
    description: Optional[str],
    format_name: str,
    vinyl_variant: str,
    price: float,
    product_id: str,
    unsubscribe_token: str,
    subscriber_name: Optional[str] = None,
) -> str:
    """Plain-text email fallback."""
    app_url = settings.PUBLIC_APP_URL.rstrip("/")
    product_url = f"{app_url}/products/{product_id}"
    unsubscribe_url = f"{app_url}/newsletter/unsubscribe?token={unsubscribe_token}"
    greeting = f"Good morning, {subscriber_name.strip()}" if subscriber_name and subscriber_name.strip() else "Good morning"
    variant_display = vinyl_variant.replace("_", " ").title() if vinyl_variant else "Standard Black"

    return f"""OTOICHI (音市) - LETTERS FROM THE LISTENING ROOM
Every Monday, one record worth hearing.
--------------------------------------------------

{greeting},

This week's selected vinyl pressing:
{album_title}
by {artist_name}

Format: {format_name} ({variant_display})
Price: ${price:.2f} USD

{description or 'A singular acoustic master pressing, inspected under Goldmine Grading standards.'}

Inspect the pressing, tracklist, and audio preview:
{product_url}

--------------------------------------------------
To unsubscribe from this weekly newsletter:
{unsubscribe_url}

Otoichi (音市) - Kyoto & Tokyo Sound Archives
{app_url}
"""
