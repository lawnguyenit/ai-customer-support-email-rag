"""
Test Fixtures and Knowledge Base for AI Customer Support Email Workflow
Includes 7 representative test scenarios matching the Upwork client brief.
"""

KNOWLEDGE_BASE_ARTICLES = [
    {
        "id": "kb_doc_001",
        "title": "Refund Policy and Billing Terms",
        "category": "billing_refund",
        "text": (
            "Refund Policy: Customers are eligible for a 100% full refund within 14 days of initial purchase "
            "if they have encountered technical issues or are dissatisfied with the service. To request a refund, "
            "customers must email billing@agency.com with their order ID. Refunds are processed back to the original "
            "payment method within 3 to 5 business days."
        ),
        "keywords": ["refund", "billing", "money back", "cancel subscription", "14 days", "order id", "payment method"]
    },
    {
        "id": "kb_doc_002",
        "title": "Account Password Reset and MFA Troubleshooting",
        "category": "account_access",
        "text": (
            "Password Reset: Users can reset their password by visiting https://app.agency.com/forgot-password. "
            "A reset token is sent to the registered email and is valid for 30 minutes. If 2FA/MFA token is lost, "
            "the user must contact an account administrator to generate a temporary recovery code."
        ),
        "keywords": ["password", "reset", "login", "mfa", "2fa", "account access", "locked out"]
    },
    {
        "id": "kb_doc_003",
        "title": "API Rate Limits and Quotas",
        "category": "technical_issue",
        "text": (
            "API Rate Limits: Standard plan accounts are limited to 60 requests per minute and 10,000 requests per day. "
            "Enterprise tier accounts enjoy up to 600 requests per minute. When rate limits are exceeded, the API returns "
            "HTTP 429 Too Many Requests with a Retry-After header indicating wait time in seconds."
        ),
        "keywords": ["api", "rate limit", "quota", "429", "too many requests", "throttle"]
    },
    {
        "id": "kb_doc_004",
        "title": "Supported Webhook and Email Integrations",
        "category": "feature_question",
        "text": (
            "Supported Integrations: Our automation platform supports native webhooks, Gmail, Google Sheets, "
            "Slack, HubSpot, and PostgreSQL. Custom REST endpoints can be connected via HTTP Request nodes with "
            "Header Auth or OAuth2."
        ),
        "keywords": ["integration", "webhook", "gmail", "slack", "hubspot", "connect"]
    }
]

TEST_SCENARIOS = [
    {
        "scenario_id": "TC_01",
        "name": "Support Email with Relevant Knowledge Base Match",
        "description": "Customer inquires about refund within 14 days; KB has exact match.",
        "input_email": {
            "message_id": "<msg-20261026-001@customer.org>",
            "thread_id": "thread_alpha_101",
            "sender_email": "jane.doe@example.com",
            "sender_name": "Jane Doe",
            "subject": "Inquiry about refund policy for Order #88219",
            "body": "Hello support team, I purchased your service 4 days ago but our requirements changed. Can I still get a refund? How many days does it take to process?",
            "received_timestamp": "2026-10-26T10:00:00Z"
        },
        "expected_result": {
            "is_support": True,
            "category": "billing_refund",
            "min_similarity_score": 0.75,
            "routed_to": "AI_RESPONSE_GENERATION",
            "reply_preserved_thread": True,
            "reply_contains": ["14 days", "3 to 5 business days", "billing@agency.com"]
        }
    },
    {
        "scenario_id": "TC_02",
        "name": "Non-Support Email (Cold Sales Outreach / Spam)",
        "description": "Incoming sales pitch offering SEO / outsourced services. Must be ignored cleanly.",
        "input_email": {
            "message_id": "<sales-pitch-999@growthspammer.io>",
            "thread_id": "thread_spam_202",
            "sender_email": "growth@growthspammer.io",
            "sender_name": "Growth Hacker",
            "subject": "Guaranteed 10x SEO traffic for your agency in 30 days!",
            "body": "Hi there, Do you want to rank #1 on Google? We provide 500 high-DA backlinks. Let me know if you are open for a quick 15-min call this Thursday.",
            "received_timestamp": "2026-10-26T10:05:00Z"
        },
        "expected_result": {
            "is_support": False,
            "category": "non_support",
            "routed_to": "EXIT_CLEANLY_NO_REPLY",
            "sent_reply": False
        }
    },
    {
        "scenario_id": "TC_03",
        "name": "Support Email with Insufficient Knowledge (Human Escalation)",
        "description": "Customer asks about an obscure feature not in the knowledge base.",
        "input_email": {
            "message_id": "<msg-obscure-303@techcorp.com>",
            "thread_id": "thread_escalate_303",
            "sender_email": "cto@techcorp.com",
            "sender_name": "Dr. Aris Thorne",
            "subject": "Support for Quantum Encryption Hardware Modules (HSM)",
            "body": "Greetings, Does your platform support on-premise hardware security module (HSM) deployment for quantum-resistant lattice key storage?",
            "received_timestamp": "2026-10-26T10:10:00Z"
        },
        "expected_result": {
            "is_support": True,
            "category": "technical_issue",
            "max_similarity_score": 0.70,  # Below 0.72 threshold
            "routed_to": "HUMAN_ESCALATION",
            "label_added": "Needs-Human-Review",
            "internal_alert_triggered": True,
            "auto_reply_sent": False
        }
    },
    {
        "scenario_id": "TC_04",
        "name": "Gmail Thread Continuity (Multi-Turn Conversation)",
        "description": "Follow-up email continuing an existing thread. Response must retain threadId and RFC headers.",
        "input_email": {
            "message_id": "<msg-followup-404@customer.org>",
            "thread_id": "thread_alpha_101",  # Same thread as TC_01!
            "sender_email": "jane.doe@example.com",
            "sender_name": "Jane Doe",
            "subject": "Re: Inquiry about refund policy for Order #88219",
            "body": "Thank you! To clarify, do I also need to return the digital license certificate?",
            "received_timestamp": "2026-10-26T10:15:00Z"
        },
        "expected_result": {
            "is_support": True,
            "thread_id": "thread_alpha_101",
            "in_reply_to_header": "<msg-followup-404@customer.org>",
            "references_header": "<msg-followup-404@customer.org>",
            "thread_continuity_verified": True
        }
    },
    {
        "scenario_id": "TC_05",
        "name": "Account Access & Password Reset Request",
        "description": "Customer locked out of their dashboard, requesting urgent reset guidance.",
        "input_email": {
            "message_id": "<msg-pwd-505@usermail.com>",
            "thread_id": "thread_pwd_505",
            "sender_email": "michael.scott@dunder.com",
            "sender_name": "Michael Scott",
            "subject": "Locked out of my agency account - password reset token expired",
            "body": "I forgot my password and the token expired after 30 minutes. How can I get back in?",
            "received_timestamp": "2026-10-26T10:20:00Z"
        },
        "expected_result": {
            "is_support": True,
            "category": "account_access",
            "min_similarity_score": 0.75,
            "routed_to": "AI_RESPONSE_GENERATION",
            "reply_contains": ["forgot-password", "30 minutes", "recovery code"]
        }
    },
    {
        "scenario_id": "TC_06",
        "name": "Integration Failure Simulation (Provider Rate Limit / 429)",
        "description": "Simulate external API outage or rate limit. Must trigger error boundary without losing context.",
        "input_email": {
            "message_id": "<msg-err-606@test.com>",
            "thread_id": "thread_err_606",
            "sender_email": "test.user@test.com",
            "sender_name": "Test User",
            "subject": "API question triggering simulated failure",
            "body": "Simulated error test case",
            "received_timestamp": "2026-10-26T10:25:00Z"
        },
        "simulate_fault": "OPENAI_429_RATE_LIMIT",
        "expected_result": {
            "error_caught": True,
            "routed_to": "ERROR_HANDLER",
            "label_added": "System-Error-Review",
            "no_customer_trace_leak": True
        }
    },
    {
        "scenario_id": "TC_07",
        "name": "API Quotas & Technical Issue Inquiry",
        "description": "Developer asking why their API returns HTTP 429 and what limits apply.",
        "input_email": {
            "message_id": "<msg-tech-707@devstudio.com>",
            "thread_id": "thread_tech_707",
            "sender_email": "alex.dev@devstudio.com",
            "sender_name": "Alex Dev",
            "subject": "Getting 429 Too Many Requests on standard webhook endpoints",
            "body": "Hey team, we are hitting 429 errors when making around 70 calls a minute. What are the rate limits for the standard plan?",
            "received_timestamp": "2026-10-26T10:30:00Z"
        },
        "expected_result": {
            "is_support": True,
            "category": "technical_issue",
            "min_similarity_score": 0.80,
            "routed_to": "AI_RESPONSE_GENERATION",
            "reply_contains": ["60 requests per minute", "10,000 requests per day", "Retry-After"]
        }
    }
]
