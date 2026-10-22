# Storyboarder — Rule-Based Implementation

The Storyboarder uses deterministic Python logic to transform
the scene-structured script into storyboard entries.

It does not currently invoke an LLM and therefore has no
system/user LLM prompt template.

Source: agents/storyboarder.py

Input: outputs/script.json
Output: outputs/storyboard.json

This stage should be described as a rule-based agent,
not an independently reasoning LLM agent.
