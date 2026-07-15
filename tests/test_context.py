"""Tests for the user context model and intent inference."""

import pytest

from stadium_assistant.context import (
    AccessibilityNeed,
    Intent,
    Role,
    UserContext,
    infer_intent,
)


def test_language_is_normalized():
    ctx = UserContext(message="hi", language="es-MX")
    assert ctx.language == "es"


def test_unknown_language_falls_back_to_english():
    ctx = UserContext(message="hi", language="xx")
    assert ctx.language == "en"


def test_duplicate_needs_are_deduped_in_order():
    ctx = UserContext(
        message="hi",
        accessibility_needs=[
            AccessibilityNeed.MOBILITY,
            AccessibilityNeed.MOBILITY,
            AccessibilityNeed.VISION,
        ],
    )
    assert ctx.accessibility_needs == [
        AccessibilityNeed.MOBILITY,
        AccessibilityNeed.VISION,
    ]


def test_empty_message_is_rejected_by_model():
    with pytest.raises(ValueError):
        UserContext(message="")


def test_default_role_is_fan():
    assert UserContext(message="hi").role == Role.FAN


def test_infer_navigation_intent():
    assert infer_intent("where is my gate?") == Intent.NAVIGATION


def test_infer_services_intent():
    assert infer_intent("where is the nearest first aid station") in (
        Intent.SERVICES,
        Intent.NAVIGATION,
    )


def test_infer_transport_intent():
    assert infer_intent("is there accessible parking near the gate") in (
        Intent.TRANSPORT,
        Intent.ACCESSIBILITY,
    )


def test_infer_sustainability_intent():
    assert infer_intent("where can I recycle my bottle") == Intent.SUSTAINABILITY


def test_no_keywords_returns_general():
    assert infer_intent("hello there") == Intent.GENERAL


def test_needs_upgrade_navigation_to_accessibility():
    # A plain navigation question from a mobility user becomes an
    # accessibility request so step-free routing is prioritised.
    result = infer_intent("how do i get to section 108", [AccessibilityNeed.MOBILITY])
    assert result == Intent.ACCESSIBILITY
