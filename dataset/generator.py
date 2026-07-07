"""
Realistic Business Email Dataset Generator

Generates ~1000 diverse email/reply pairs across 15 categories.
Each sample contains all required fields with realistic variation.

Design principles:
- Each category has its own pool of realistic scenarios
- Entities are customer-specific (names, order IDs, amounts)
- Tones vary within categories (frustrated vs polite customers)
- Actions reflect real business processes
- Tags enable faceted search and filtering
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
OUTPUT_PATH = Path(__file__).parent / "emails.json"
TARGET_COUNT = 1000
SEED = 42
random.seed(SEED)

# ── Name / entity pools ───────────────────────────────────────────────────────
FIRST_NAMES = [
    "James", "Emma", "Oliver", "Sophia", "William", "Ava", "Benjamin", "Isabella",
    "Lucas", "Mia", "Henry", "Charlotte", "Alexander", "Amelia", "Mason", "Harper",
    "Ethan", "Evelyn", "Daniel", "Abigail", "Michael", "Emily", "Matthew", "Elizabeth",
    "Aiden", "Mila", "Jackson", "Ella", "Sebastian", "Luna", "Logan", "Nora",
    "David", "Lily", "Joseph", "Eleanor", "Samuel", "Scarlett", "Carter", "Chloe",
    "Owen", "Victoria", "Wyatt", "Riley", "John", "Aria", "Jack", "Zoey",
    "Luke", "Penelope", "Jayden", "Sofia", "Dylan", "Camila", "Grayson", "Layla",
    "Liam", "Avery", "Noah", "Stella", "Elijah", "Hannah", "Amir", "Priya",
    "Chen", "Yuki", "Mohammed", "Fatima", "Carlos", "Maria", "Raj", "Ananya",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Patel", "Kumar", "Shah", "Singh", "Chen",
    "Wang", "Kim", "Park", "Nakamura", "Yamamoto", "Cohen", "Levy", "Müller",
]

PRODUCTS = [
    "ProMax Laptop", "CloudSync Pro", "DataVault Storage", "StreamKit Camera",
    "SmartHub Controller", "EchoDesk Speaker", "PowerCell Battery Pack",
    "VisionClear Monitor", "QuietType Keyboard", "SwiftClick Mouse",
    "NeuralPad Drawing Tablet", "AeroFlow Router", "SafeVault Firewall",
    "ComfortSeat Ergonomic Chair", "FocusLens Webcam", "ThermalCore CPU Cooler",
    "CloudDesk Software Suite", "SecurePass Manager", "DataSync API",
    "AnalyticsPro Dashboard", "TeamFlow Collaboration Tool", "InvoiceWave Platform",
]

COMPANIES = [
    "TechCorp Solutions", "Nexus Dynamics", "AlphaVentures", "Quantum Systems",
    "CloudBase Inc", "DataForge Ltd", "InnovateTech", "PrimeEdge Software",
    "Apex Digital", "CoreMetrics", "BrightPath Analytics", "ZenithCloud",
    "Vertex Solutions", "Meridian Technologies", "Pinnacle Systems",
]


def _name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _email(name: str) -> str:
    parts = name.lower().split()
    formats = [
        f"{parts[0]}.{parts[1]}@example.com",
        f"{parts[0]}{parts[1][0]}@gmail.com",
        f"{parts[1]}.{parts[0]}@company.com",
        f"{parts[0]}_{parts[1]}@business.net",
    ]
    return random.choice(formats)


def _order_id() -> str:
    return f"ORD-{random.randint(100000, 999999)}"


def _ticket_id() -> str:
    return f"TKT-{random.randint(10000, 99999)}"


def _invoice_id() -> str:
    return f"INV-{random.randint(20000, 89999)}"


def _date_past(days_range: tuple[int, int] = (1, 30)) -> str:
    d = datetime.now() - timedelta(days=random.randint(*days_range))
    return d.strftime("%B %d, %Y")


def _amount() -> str:
    return f"${random.choice([29.99, 49.99, 79.99, 99.99, 149.99, 199.99, 299.99, 399.99, 499.99, 999.99]):.2f}"


def _days() -> str:
    return str(random.choice([1, 2, 3, 5, 7, 10, 14]))


def _product() -> str:
    return random.choice(PRODUCTS)


def _company() -> str:
    return random.choice(COMPANIES)


# ── Template generators for each category ─────────────────────────────────────

def gen_refund() -> dict:
    name = _name()
    order = _order_id()
    amount = _amount()
    product = _product()
    date = _date_past((3, 20))
    tone = random.choice(["frustrated", "polite", "urgent"])

    frustration_phrases = {
        "frustrated": f"I am extremely disappointed and demand an immediate refund.",
        "polite": f"I would kindly appreciate a refund for this order.",
        "urgent": f"This is urgent — I need this refund processed immediately.",
    }

    body = f"""Dear Customer Support,

I am writing regarding my recent order {order} placed on {date} for a {product} worth {amount}.

Unfortunately, the product I received does not match what was advertised on your website. The color is completely wrong and the product quality is significantly below expectations. {frustration_phrases[tone]}

I have attached photos for your reference. Please confirm the refund timeline.

Best regards,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for reaching out to us regarding order {order}. I completely understand how frustrating this situation must be, and I sincerely apologize for the inconvenience caused.

After reviewing your case, I can confirm that your refund of {amount} has been approved and will be processed within 5-7 business days to your original payment method. You will receive a confirmation email once the refund is initiated.

If you haven't received the refund after 7 business days, please don't hesitate to contact us again and reference ticket number {_ticket_id()}.

We truly value your business and hope to serve you better in the future.

Best regards,
Customer Support Team"""

    return {
        "category": "Refund",
        "intent": "refund_request",
        "tone": tone,
        "priority": "high" if tone == "frustrated" else "medium",
        "subject": f"Refund Request for Order {order} - {product}",
        "sender": _email(name),
        "recipient": "support@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "order_id": order, "amount": amount, "product": product, "date": date},
        "expected_actions": ["approve_refund", "send_confirmation_email", "provide_timeline"],
        "tags": ["refund", "product_quality", "return", tone],
    }


def gen_shipping() -> dict:
    name = _name()
    order = _order_id()
    product = _product()
    date = _date_past((5, 15))
    tracking = f"TRK{random.randint(1000000000, 9999999999)}"
    estimated_days = random.randint(2, 7)

    body = f"""Hello,

I placed an order ({order}) on {date} for a {product}, but I still haven't received it. 
The estimated delivery was {_date_past((1, 5))} and it's now been over a week.

Can you please provide an update on my order status and tracking information?

Thank you,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for contacting us about your order {order}. I understand how concerning it can be when a package doesn't arrive as expected, and I apologize for any anxiety this has caused.

I've looked into your order and I'm pleased to let you know that your {product} was dispatched from our warehouse on {_date_past((3, 5))}. Here are your shipment details:

• Tracking Number: {tracking}
• Current Status: In Transit
• Estimated Delivery: {estimated_days} business days from today

You can track your package in real-time at our tracking portal. If your package does not arrive within {estimated_days + 2} business days, please contact us immediately and we will arrange a replacement or full refund.

We appreciate your patience and apologize for the delay.

Best regards,
Shipping Support Team"""

    return {
        "category": "Shipping",
        "intent": "shipping_inquiry",
        "tone": "concerned",
        "priority": "medium",
        "subject": f"Where is my order {order}?",
        "sender": _email(name),
        "recipient": "support@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "order_id": order, "product": product, "tracking_number": tracking},
        "expected_actions": ["provide_tracking_info", "give_delivery_estimate", "offer_resolution"],
        "tags": ["shipping", "delivery", "tracking", "late_delivery"],
    }


def gen_billing() -> dict:
    name = _name()
    amount = _amount()
    invoice = _invoice_id()
    date = _date_past((1, 10))

    body = f"""Dear Billing Department,

I noticed an unexpected charge of {amount} on my account dated {date}. This does not correspond to any subscription or purchase I am aware of.

My account email is {_email(name)} and the invoice number appears to be {invoice}.

Please investigate this charge and provide a detailed explanation. If it is an error, I expect an immediate reversal.

Regards,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for bringing this billing discrepancy to our attention. I completely understand your concern about an unexpected charge, and I want to assure you we take billing accuracy very seriously.

I have reviewed invoice {invoice} dated {date} for {amount}. Our billing team has been notified and will conduct a thorough investigation within 2 business days.

In the meantime, I have placed a temporary hold on any further charges related to this invoice. Once the investigation is complete, if the charge is confirmed as an error, we will:

1. Issue a full reversal of {amount} to your account
2. Send you an updated invoice with correct details
3. Provide a written explanation of what caused the discrepancy

You will receive an email update within 48 hours. If you need to reach us sooner, please reference case number {_ticket_id()}.

Sincerely,
Billing Support Team"""

    return {
        "category": "Billing",
        "intent": "billing_dispute",
        "tone": "concerned",
        "priority": "high",
        "subject": f"Unexpected Charge on Account - {invoice}",
        "sender": _email(name),
        "recipient": "billing@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "amount": amount, "invoice_id": invoice, "date": date},
        "expected_actions": ["investigate_charge", "place_hold", "provide_timeline", "send_case_number"],
        "tags": ["billing", "dispute", "unexpected_charge", "invoice"],
    }


def gen_technical_support() -> dict:
    name = _name()
    product = _product()
    error_codes = ["ERR-500", "AUTH-403", "CONN-TIMEOUT", "DB-LOCK", "API-429", "SSL-CERT-INVALID"]
    error = random.choice(error_codes)
    ticket = _ticket_id()

    body = f"""Hi Support Team,

I'm experiencing a critical issue with {product} that is blocking my entire workflow. 

When I try to access the dashboard, I get error code: {error}. This started happening yesterday afternoon and I've already tried:
- Clearing browser cache
- Using a different browser (Chrome, Firefox, Edge)
- Restarting the application
- Checking firewall settings

None of these solutions have worked. This is severely impacting my productivity. Please help urgently.

Thanks,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for reporting this issue with {product}. I understand how disruptive a technical problem can be to your workflow, and I've escalated this to our Level 2 Technical Team immediately.

Your support ticket {ticket} has been created with HIGH priority.

Regarding error code {error}, our initial analysis suggests this may be related to a server-side configuration. While our engineers investigate, here are some targeted steps that may resolve this:

1. **Clear Application Data**: Go to Settings → Storage → Clear Application Data
2. **Disable Extensions**: Try accessing in Incognito mode with all extensions disabled
3. **Check Status Page**: Visit status.company.com for any known service disruptions
4. **Use Alternative Access**: Try accessing via our mobile app if available

Our engineering team will have a definitive diagnosis within 4 hours. You will receive a status update via email and can track progress at support.company.com using ticket {ticket}.

We sincerely apologize for this disruption.

Best regards,
Technical Support Team | Priority Queue"""

    return {
        "category": "Technical Support",
        "intent": "technical_issue",
        "tone": "urgent",
        "priority": "critical",
        "subject": f"URGENT: {product} - Error {error} Blocking Workflow",
        "sender": _email(name),
        "recipient": "techsupport@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product, "error_code": error, "ticket_id": ticket},
        "expected_actions": ["create_ticket", "escalate_to_engineering", "provide_workarounds", "set_sla"],
        "tags": ["technical", "error", "critical", "escalation", error.lower()],
    }


def gen_password_reset() -> dict:
    name = _name()
    email_addr = _email(name)

    body = f"""Hello,

I've been locked out of my account associated with email {email_addr}. I tried resetting my password but I'm not receiving the reset email. I've checked my spam folder as well.

I need access urgently as I have important files stored in my account. 

Please help me recover access as soon as possible.

Thank you,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for reaching out, and I'm sorry to hear you're having trouble accessing your account. Account security is our top priority, so let me help you regain access safely.

I've verified your account associated with {email_addr} and have initiated a manual password reset. Please follow these steps:

1. **Check your inbox for {email_addr}** — a secure reset link has been sent. This link is valid for 24 hours.
2. If you don't receive it within 5 minutes, check your Spam/Junk folder
3. The email will come from noreply@company.com — please add this to your safe senders list

**If the email still doesn't arrive**, please:
- Try an alternative email address if you registered with one
- Reply to this email with your account creation date for additional verification

For security reasons, we cannot provide account access through email. The secure link is the only approved method.

Please let us know if you need any further assistance.

Best regards,
Account Security Team"""

    return {
        "category": "Password Reset",
        "intent": "account_recovery",
        "tone": "urgent",
        "priority": "high",
        "subject": "Cannot Access Account - Password Reset Not Working",
        "sender": email_addr,
        "recipient": "security@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "email": email_addr},
        "expected_actions": ["trigger_password_reset", "verify_identity", "provide_instructions"],
        "tags": ["password", "account_access", "locked_out", "security"],
    }


def gen_cancellation() -> dict:
    name = _name()
    product = _product()
    amount = _amount()
    reason = random.choice([
        "too expensive", "not using it enough", "switching to a competitor",
        "budget cuts", "missing key features", "poor customer service experience",
    ])

    body = f"""Dear Team,

I would like to cancel my subscription to {product} ({amount}/month). My reason for cancellation is that it is {reason}.

Please confirm the cancellation and let me know if there's anything I need to do on my end.

Also, please confirm whether I will receive a prorated refund for the unused portion of this billing period.

Thanks,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for reaching out, and I'm sorry to hear you'd like to cancel your {product} subscription. I completely respect your decision, though I'd love to understand if there's anything we could do to address your concern about "{reason}".

Before I process your cancellation, I'd like to offer you:
- **A 30-day free extension** to reconsider at no cost
- **A downgrade to our basic plan** at 50% of your current cost
- **A personalized demo** with our team to address any feature gaps

If you'd still like to proceed with cancellation, I will:
1. Cancel your subscription effective at the end of your current billing period
2. Issue a prorated refund of {_amount()} for unused days (you will receive this within 5-7 days)
3. Send you a cancellation confirmation email

Please reply confirming your decision, and I'll process it immediately. Your data will be retained for 30 days after cancellation in case you change your mind.

We're sorry to see you go and hope to welcome you back in the future.

Best regards,
Customer Success Team"""

    return {
        "category": "Cancellation",
        "intent": "subscription_cancellation",
        "tone": "formal",
        "priority": "high",
        "subject": f"Cancel Subscription - {product}",
        "sender": _email(name),
        "recipient": "accounts@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product, "amount": amount, "reason": reason},
        "expected_actions": ["offer_retention", "confirm_cancellation", "process_refund", "retain_data"],
        "tags": ["cancellation", "subscription", "churn", reason.replace(" ", "_")],
    }


def gen_sales() -> dict:
    name = _name()
    company = _company()
    product = _product()
    team_size = random.choice([10, 25, 50, 100, 250, 500])

    body = f"""Hi there,

I'm {name}, Head of Technology at {company}. We're a team of {team_size} people looking to evaluate solutions for our infrastructure needs.

I came across {product} and I'm interested in understanding:
1. Pricing for enterprise teams
2. Integration capabilities with AWS and Azure
3. Compliance certifications (SOC 2, ISO 27001)
4. Implementation timeline and support

Can we schedule a demo or call this week?

Best,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you for your interest in {product}! I'm excited to connect with you and learn more about {company}'s needs.

Here's a quick overview based on your questions:

**Enterprise Pricing**
Our enterprise plans start at {_amount()}/month for up to {team_size} users, with custom pricing available for larger deployments. Volume discounts apply for annual commitments.

**Integrations**
{product} has native integrations with AWS (EC2, S3, RDS), Azure (VM, Blob Storage, Azure AD), and 50+ other enterprise tools via our REST API.

**Compliance**
We hold the following certifications:
- SOC 2 Type II ✓
- ISO 27001 ✓  
- GDPR Compliant ✓
- HIPAA Ready ✓

**Implementation**
Typical enterprise deployments take 2-4 weeks with dedicated onboarding support.

I'd love to set up a 30-minute discovery call to understand your specific requirements and show you a personalized demo. Are you available for a call this Thursday or Friday?

Looking forward to connecting!

Best regards,
Enterprise Sales Team"""

    return {
        "category": "Sales",
        "intent": "sales_inquiry",
        "tone": "professional",
        "priority": "high",
        "subject": f"Enterprise Inquiry - {product} for {company}",
        "sender": _email(name),
        "recipient": "sales@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "company": company, "product": product, "team_size": str(team_size)},
        "expected_actions": ["provide_pricing", "explain_integrations", "confirm_compliance", "schedule_demo"],
        "tags": ["sales", "enterprise", "b2b", "demo_request", "pricing"],
    }


def gen_enterprise() -> dict:
    name = _name()
    company = _company()
    product = _product()
    seats = random.choice([100, 250, 500, 1000, 2500])

    body = f"""Dear Account Executive,

We are currently in contract renewal discussions for our {seats}-seat {product} enterprise license. Before we proceed, our procurement team requires:

1. Updated SLA documentation (99.9% uptime guarantee details)
2. Data Processing Agreement (DPA) for GDPR compliance
3. Renewal pricing for {seats} seats with multi-year discount
4. Security questionnaire completion (attached)

The contract expires in 30 days. Please have your legal and enterprise teams coordinate on these items.

Best regards,
{name}
VP of Operations, {company}"""

    reply = f"""Dear {name.split()[0]},

Thank you for initiating the renewal process for your {company} enterprise account. We greatly value our partnership and want to ensure a seamless renewal for your {seats}-seat {product} deployment.

I'm coordinating with our Legal, Enterprise, and Security teams immediately on all four items:

1. **SLA Documentation**: I'll have our updated SLA with 99.9% uptime guarantee and financial remedies sent within 24 hours.

2. **Data Processing Agreement**: Our standard DPA (GDPR Article 28 compliant) will be sent for review. We can also negotiate custom terms if required.

3. **Renewal Pricing**: For {seats} seats, I'm preparing a proposal with:
   - 1-year term: standard renewal rate
   - 2-year term: 12% discount
   - 3-year term: 20% discount
   I'll have the formal proposal ready by tomorrow EOD.

4. **Security Questionnaire**: Our Security team will complete the attached questionnaire within 3 business days.

Given the 30-day window, I've set your account to priority status. Would you be available for a 30-minute call this week to align on timeline and terms?

Best regards,
Enterprise Account Team"""

    return {
        "category": "Enterprise",
        "intent": "contract_renewal",
        "tone": "formal",
        "priority": "critical",
        "subject": f"Enterprise License Renewal - {company} ({seats} seats)",
        "sender": _email(name),
        "recipient": "enterprise@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "company": company, "product": product, "seats": str(seats)},
        "expected_actions": ["send_sla", "send_dpa", "prepare_pricing_proposal", "complete_security_questionnaire"],
        "tags": ["enterprise", "contract", "renewal", "legal", "compliance"],
    }


def gen_pricing() -> dict:
    name = _name()
    product = _product()
    competitor = random.choice(["Competitor A", "CompetitorX", "a competing solution"])

    body = f"""Hi,

I'm evaluating {product} against {competitor}. Your product seems strong but I can't find clear pricing on your website.

Could you explain:
- What's included in each pricing tier?
- Do you offer a free trial?
- Are there discounts for nonprofits or startups?
- What are the overage charges if we exceed limits?

I'd like to make a decision by end of this week.

{name}"""

    tiers = [
        ("Starter", "$19/month", "5 users, 10GB storage"),
        ("Professional", "$49/month", "25 users, 100GB storage + API access"),
        ("Business", "$149/month", "Unlimited users, 1TB storage + advanced analytics"),
        ("Enterprise", "Custom", "Everything + dedicated support + SLA"),
    ]

    reply = f"""Dear {name.split()[0]},

Thank you for your interest in {product}! I'm happy to provide a complete pricing breakdown.

**Pricing Tiers**

| Plan | Price | Includes |
|------|-------|----------|
| {tiers[0][0]} | {tiers[0][1]} | {tiers[0][2]} |
| {tiers[1][0]} | {tiers[1][1]} | {tiers[1][2]} |
| {tiers[2][0]} | {tiers[2][1]} | {tiers[2][2]} |
| {tiers[3][0]} | {tiers[3][1]} | {tiers[3][2]} |

**Free Trial**: Yes! All plans include a 14-day free trial, no credit card required.

**Special Discounts**:
- Nonprofits: 30% off any plan (501(c)3 verification required)
- Startups (<3 years, <50 employees): 20% off for first year
- Annual billing: 2 months free (equivalent to ~17% savings)

**Overage Charges**: Storage overages are billed at $0.10/GB/month. User overages vary by plan.

Given your timeline, I'd recommend starting your free trial today. I can also arrange a quick 15-minute call to help you choose the right tier.

Best regards,
Sales Team"""

    return {
        "category": "Pricing",
        "intent": "pricing_inquiry",
        "tone": "friendly",
        "priority": "medium",
        "subject": f"Pricing Question - {product}",
        "sender": _email(name),
        "recipient": "sales@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product},
        "expected_actions": ["provide_pricing_tiers", "mention_free_trial", "mention_discounts", "offer_assistance"],
        "tags": ["pricing", "free_trial", "discount", "evaluation"],
    }


def gen_bug_report() -> dict:
    name = _name()
    product = _product()
    bug_types = [
        ("data not saving", "When I click Save, the form submits but data is lost on refresh"),
        ("export broken", "The PDF export function produces blank pages"),
        ("login loop", "After logging in, I'm immediately redirected back to the login page"),
        ("calculation error", "The invoice total shows incorrect tax calculation"),
        ("UI overlap", "Buttons are overlapping on mobile Safari browsers"),
    ]
    bug_type, description = random.choice(bug_types)

    body = f"""Hi Support,

I've found a bug in {product} that is affecting my work.

Bug: {bug_type.title()}
Description: {description}
Browser/OS: Chrome {random.randint(110, 120)}.0 on Windows 11
Account: {_email(name)}
Steps to reproduce:
1. Log in to your account
2. Navigate to the affected section
3. Perform the action
4. Observe the issue

This is happening consistently and affecting my team. Please prioritize fixing this.

Thanks,
{name}"""

    ticket = _ticket_id()

    reply = f"""Dear {name.split()[0]},

Thank you for reporting this bug with such detailed information — this is incredibly helpful for our engineering team!

I've created a bug report (ticket {ticket}) and assigned it to our engineering team with MEDIUM-HIGH priority.

**Current Status**: Under Investigation

Your bug details have been logged:
- Issue: {bug_type.title()} in {product}
- Environment: Chrome, Windows 11
- Reproducibility: Consistent (as reported)

**Immediate Workaround**: While we investigate, you may be able to work around this by [performing the action in Firefox or using our mobile app].

**Timeline**: Our team aims to have a fix deployed within 3-5 business days. You will be notified via email when a patch is released.

If you experience any other issues or the bug affects you critically, please don't hesitate to escalate by replying "ESCALATE" to this email.

Best regards,
Quality Assurance Team | Ticket {ticket}"""

    return {
        "category": "Bug Report",
        "intent": "bug_report",
        "tone": "professional",
        "priority": "medium",
        "subject": f"Bug Report: {bug_type.title()} in {product}",
        "sender": _email(name),
        "recipient": "bugs@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product, "ticket_id": ticket, "bug_type": bug_type},
        "expected_actions": ["create_bug_ticket", "assign_to_engineering", "provide_workaround", "set_timeline"],
        "tags": ["bug", "technical", bug_type.replace(" ", "_"), "engineering"],
    }


def gen_feature_request() -> dict:
    name = _name()
    product = _product()
    features = [
        "dark mode", "bulk export to CSV", "two-factor authentication via SMS",
        "custom reporting dashboards", "webhook integrations", "offline mode",
        "keyboard shortcuts", "white-label branding", "API rate limit increase",
        "multi-language support", "advanced filtering", "audit logs",
    ]
    feature = random.choice(features)

    body = f"""Hello,

I've been using {product} for {random.randint(6, 36)} months and I love it! However, I have a feature request that I think would be extremely valuable:

**{feature.title()}**

Here's why this would be valuable:
- It would save our team approximately {random.randint(2, 10)} hours per week
- Our entire team has requested this
- It's a standard feature in many competing tools

Is this on your roadmap? If not, can you please consider adding it?

Happy user,
{name}"""

    reply = f"""Dear {name.split()[0]},

Thank you so much for being a loyal {product} user and for taking the time to submit this feature request! We genuinely value feedback from our community.

I'm happy to share that we've logged your request for **{feature.title()}** in our product feedback system. This type of input directly shapes our roadmap.

**Current Status**: Submitted to Product Team for Review

I'll be transparent about our process:
1. Your request has been added to our feature backlog with positive upvoting
2. Our Product team reviews the backlog quarterly based on community demand and strategic fit
3. If {feature} reaches our roadmap, you'll be notified before public announcement

**In the meantime**, you might find our current workaround useful: [related functionality that may partially address the need].

While I can't make specific promises about when this will be developed, I can tell you that your vote counts. If you know other users who'd benefit, encourage them to submit similar requests — volume of demand strongly influences our prioritization.

Thank you for helping us make {product} better!

Best regards,
Product Feedback Team"""

    return {
        "category": "Feature Request",
        "intent": "feature_request",
        "tone": "friendly",
        "priority": "low",
        "subject": f"Feature Request: {feature.title()} for {product}",
        "sender": _email(name),
        "recipient": "feedback@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product, "feature": feature},
        "expected_actions": ["log_feature_request", "explain_process", "set_expectations", "encourage_community"],
        "tags": ["feature_request", "product_feedback", feature.replace(" ", "_"), "roadmap"],
    }


def gen_subscription() -> dict:
    name = _name()
    product = _product()
    plan = random.choice(["Basic", "Professional", "Business", "Enterprise"])
    amount = _amount()

    action = random.choice(["upgrade", "downgrade", "pause"])

    if action == "upgrade":
        body = f"""Hello,

I'm currently on the {plan} plan for {product} at {amount}/month. I'd like to upgrade to the next tier to access advanced analytics features.

Can you:
1. Tell me what's included in the next tier
2. Confirm the price difference
3. Process the upgrade immediately?

Also, will I be billed immediately or at the next cycle?

Thanks,
{name}"""
        reply = f"""Dear {name.split()[0]},

Excellent news — I'm happy to help you upgrade your {product} subscription!

**Upgrade Details: {plan} → Professional**

What you'll gain immediately:
- Advanced Analytics & Reporting
- Priority Support Queue
- API Access (10,000 calls/month)
- Team Collaboration Features
- Custom Branding

**Billing**: The upgrade will take effect immediately. You'll be charged a prorated amount for the remainder of this billing cycle, then the full new rate at your next billing date.

Your current plan: {amount}/month → New plan: {_amount()}/month

To process your upgrade, simply click here: [Upgrade Now] (or reply "CONFIRM UPGRADE" to this email).

Your new features will be available within minutes of confirmation.

Best regards,
Subscription Team"""

    else:
        body = f"""Dear Billing,

I need to {action} my {product} subscription. I'm currently on {plan} ({amount}/month).

Please let me know the process and any implications.

Thanks,
{name}"""
        reply = f"""Dear {name.split()[0]},

Thank you for reaching out about your subscription {action}. I'm happy to assist!

I've reviewed your {plan} account and can process your request immediately.

**{action.title()} Details**:
- Your subscription will be {action}d effective today
- Billing adjustments will reflect in your next invoice
- Any features not available in your new plan will remain accessible until end of current period

Is there anything specific that prompted this change? We have options that might better suit your needs, including:
- A personalized plan at a different price point
- A temporary pause option if you need a break

Please reply to confirm you'd like to proceed with the {action}.

Best regards,
Subscription Management Team"""

    return {
        "category": "Subscription",
        "intent": f"subscription_{action}",
        "tone": "professional",
        "priority": "medium",
        "subject": f"Subscription {action.title()} Request - {product}",
        "sender": _email(name),
        "recipient": "billing@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product, "plan": plan, "amount": amount},
        "expected_actions": [f"process_{action}", "explain_billing_changes", "confirm_changes"],
        "tags": ["subscription", action, "billing", plan.lower()],
    }


def gen_account_access() -> dict:
    name = _name()
    email_addr = _email(name)

    issue = random.choice([
        "two-factor authentication locked me out",
        "account suspended without warning",
        "SSO login not working after company domain change",
        "account shows different user's data",
    ])

    body = f"""Urgent: I cannot access my account and {issue}.

My email: {email_addr}
Account since: {_date_past((180, 730))}

I have important data in this account and need access restored immediately. I can verify my identity via any method you require.

Please help ASAP.

{name}"""

    reply = f"""Dear {name.split()[0]},

I understand how urgent this is, and I want to help you regain access to your account right away.

For security purposes, I've initiated our secure account recovery process for {email_addr}.

**Immediate Steps**:
1. A secure verification code has been sent to your backup email/phone on file
2. Please use this link to complete identity verification: [Secure Recovery Link] (valid 30 minutes)
3. Once verified, you'll be prompted to set new authentication credentials

**Regarding your specific issue — {issue}**:
Our security team has flagged your account for manual review. This typically resolves within 2-4 hours.

**While you wait**: If you need to access specific files or data urgently, please tell me exactly what you need and I can manually extract and send it to your verified email address.

Your ticket number is {_ticket_id()} — please reference this in any follow-up communications.

We take account security seriously and apologize for the disruption.

Best regards,
Account Security Team"""

    return {
        "category": "Account Access",
        "intent": "account_access",
        "tone": "urgent",
        "priority": "critical",
        "subject": "URGENT: Cannot Access Account",
        "sender": email_addr,
        "recipient": "security@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "email": email_addr},
        "expected_actions": ["initiate_recovery", "verify_identity", "restore_access", "create_ticket"],
        "tags": ["account_access", "security", "locked_out", "urgent"],
    }


def gen_complaint() -> dict:
    name = _name()
    product = _product()
    rep_name = _name()

    complaints = [
        (f"I was told by your representative {rep_name} that I would receive a refund within 2 days. It's been 3 weeks and nothing has happened. Every time I call, I get a different story.", "broken_promise"),
        (f"The quality of {product} has noticeably declined in the last 3 months. I've been a customer for years and this is unacceptable.", "quality_decline"),
        (f"I spent 4 hours on hold yesterday trying to reach customer support. When I finally got through, the agent was rude and unhelpful.", "poor_support"),
    ]
    complaint_text, complaint_type = random.choice(complaints)

    body = f"""I am writing to formally express my dissatisfaction with your service.

{complaint_text}

I am extremely disappointed. I have been a loyal customer for {random.randint(1, 5)} years and this experience has made me seriously consider switching to a competitor.

I expect a response within 24 hours and a concrete plan to resolve this situation.

{name}"""

    reply = f"""Dear {name.split()[0]},

I want to begin by sincerely apologizing for the experience you've described. Reading your email, I can clearly see that we have failed to meet the standards you rightfully expect from us, and I am genuinely sorry.

This is completely unacceptable and I am personally taking ownership of your case.

Here is what I am doing right now:

**Immediate Actions**:
1. I have flagged your account as a priority case (reference: {_ticket_id()})
2. I have escalated directly to our Customer Experience Manager who will personally oversee your resolution
3. I am reviewing the complete history of your interactions with us

**What happens next**:
- You will receive a personal call within 4 business hours from our Customer Experience team
- A written resolution plan will be provided within 24 hours
- As a gesture of our commitment to making this right, I am applying a goodwill credit to your account

Your loyalty over the years means everything to us, and I am committed to ensuring this situation is resolved in a way that restores your confidence in us.

I am truly sorry.

Sincerely,
Customer Experience Director"""

    return {
        "category": "Customer Complaint",
        "intent": "complaint",
        "tone": "frustrated",
        "priority": "critical",
        "subject": "Formal Complaint - Unacceptable Service",
        "sender": _email(name),
        "recipient": "executive@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product},
        "expected_actions": ["apologize", "escalate_to_manager", "create_priority_ticket", "apply_goodwill_credit", "schedule_callback"],
        "tags": ["complaint", "escalation", complaint_type, "customer_retention"],
    }


def gen_positive_feedback() -> dict:
    name = _name()
    product = _product()
    rep_name = _name()

    body = f"""Dear Team,

I just wanted to take a moment to say how impressed I am with {product} and especially with your support team.

I had an issue last week that {rep_name} resolved incredibly quickly and professionally. The patience and expertise shown was outstanding.

The product itself has transformed how our team works — we've seen a 40% improvement in our workflow efficiency since adopting it.

Keep up the fantastic work. You have a customer for life!

Warmly,
{name}"""

    reply = f"""Dear {name.split()[0]},

Your message has truly made our day! 😊 Thank you so much for taking the time to share this wonderful feedback — it means the world to us.

It's incredibly rewarding to hear that {product} has had such a meaningful impact on your team's efficiency. A 40% improvement is phenomenal, and it's exactly the kind of outcome we strive for.

I'll make sure {rep_name.split()[0]} receives a personal recognition for the exceptional support they provided. Our team members work incredibly hard, and knowing they're making a real difference motivates them to keep going.

**A small thank you from us**:
- We've added a 3-month complimentary upgrade to your account as a token of our appreciation
- We'd love to feature your story in our customer success section (with your permission)

Customers like you are the reason we do what we do. Thank you for being part of our journey!

With sincere gratitude,
Customer Success Team"""

    return {
        "category": "Positive Feedback",
        "intent": "positive_feedback",
        "tone": "friendly",
        "priority": "low",
        "subject": f"Fantastic Experience with {product} and Your Team!",
        "sender": _email(name),
        "recipient": "feedback@company.com",
        "incoming_email": body,
        "ideal_reply": reply,
        "entities": {"name": name, "product": product, "rep_name": rep_name},
        "expected_actions": ["acknowledge_feedback", "recognize_employee", "offer_reward", "request_testimonial"],
        "tags": ["positive_feedback", "praise", "customer_success", "testimonial"],
    }


# ── Category registry ─────────────────────────────────────────────────────────
GENERATORS = {
    "Refund": (gen_refund, 85),
    "Shipping": (gen_shipping, 80),
    "Billing": (gen_billing, 75),
    "Technical Support": (gen_technical_support, 85),
    "Password Reset": (gen_password_reset, 60),
    "Cancellation": (gen_cancellation, 65),
    "Sales": (gen_sales, 70),
    "Enterprise": (gen_enterprise, 60),
    "Pricing": (gen_pricing, 65),
    "Bug Report": (gen_bug_report, 75),
    "Feature Request": (gen_feature_request, 65),
    "Subscription": (gen_subscription, 70),
    "Account Access": (gen_account_access, 60),
    "Customer Complaint": (gen_complaint, 70),
    "Positive Feedback": (gen_positive_feedback, 55),
}


def generate_dataset(n: int = TARGET_COUNT) -> list[dict]:
    """Generate n email samples proportionally across all categories."""
    total_weight = sum(w for _, w in GENERATORS.values())
    dataset: list[dict] = []

    for category, (gen_fn, weight) in GENERATORS.items():
        count = max(1, round(n * weight / total_weight))
        for _ in range(count):
            try:
                sample = gen_fn()
                sample["id"] = len(dataset) + 1
                dataset.append(sample)
            except Exception as e:
                print(f"Warning: Failed to generate {category} sample: {e}")

    # Shuffle to avoid category clustering
    random.shuffle(dataset)

    # Trim or pad to exact count
    if len(dataset) > n:
        dataset = dataset[:n]

    print(f"Generated {len(dataset)} email samples across {len(GENERATORS)} categories")
    category_counts = {}
    for item in dataset:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

    return dataset


def main() -> None:
    output = Path(OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {TARGET_COUNT} email samples...")
    dataset = generate_dataset(TARGET_COUNT)

    with output.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\nDataset saved to {output} ({output.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
