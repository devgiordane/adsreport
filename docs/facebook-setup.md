# Facebook Setup Guide

This guide walks you through creating a Facebook Developer app and generating a long-lived access token. This takes about 5 minutes and is completely free.

## Why you need this

AdsReport operates in **Facebook Marketing API development mode** — you use your own app credentials to read your own ad data. No App Review, no Meta approval, no cost.

## Step 1: Create a Facebook Developer account

1. Go to [developers.facebook.com](https://developers.facebook.com).
2. Log in with your Facebook account.
3. Click **Get Started** if prompted.

## Step 2: Create a new app

1. Click **My Apps** → **Create App**.
2. Select **Other** as the use case, then **Business** as the app type.
3. Give it a name (e.g., `AdsReport Local`) and click **Create App**.

## Step 3: Add the Marketing API product

1. In your app dashboard, click **Add Product**.
2. Find **Marketing API** and click **Set Up**.

## Step 4: Generate an access token

1. In the left sidebar, go to **Tools** → **Graph API Explorer**.
2. Under **Facebook App**, select the app you just created.
3. Under **User or Page**, click **Generate Access Token**.
4. Check these permissions:
   - `ads_read`
   - `ads_management` (for metadata)
   - `read_insights`
   - `business_management`
5. Click **Generate Access Token** and authorize the app.

This token is short-lived (1–2 hours). Continue to Step 5 to extend it.

## Step 5: Get a long-lived token

Short-lived tokens expire quickly. You need a long-lived token (60 days) for AdsReport to work reliably.

1. Go to **Tools** → **Access Token Debugger**.
2. Paste your short-lived token and click **Debug**.
3. Click **Extend Access Token** at the bottom.
4. Copy the new long-lived token.

> **Note:** Long-lived tokens expire after 60 days. When your token expires, you'll see a sync error in AdsReport. Go to Settings → Facebook to update it.

## Step 6: Get your App ID and App Secret

1. In your app dashboard, go to **Settings** → **Basic**.
2. Copy the **App ID** and **App Secret** (click Show to reveal it).

## Step 7: Enter credentials in AdsReport

During onboarding (Step 3), enter:
- **App ID** — from Settings → Basic
- **App Secret** — from Settings → Basic
- **Access Token** — the long-lived token from Step 5

Click **Test connection**. AdsReport will verify the credentials and show a list of your ad accounts.

## Troubleshooting

**"Invalid OAuth access token"** — The token expired or was copied incorrectly. Regenerate it from Step 4.

**"No ad accounts found"** — Your Facebook user isn't an admin or analyst on any ad account. Ask the account admin to add you.

**"App not in allowed modes"** — Make sure the app is in Development mode (top bar in the dashboard shows "Development").
