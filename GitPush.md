# GitHub Push Log

This document tracks the Git commands used to push the project to GitHub step-by-step, along with their purposes.

Since the files for Steps 1 through 4 are currently all mixed together in the project folder, we will commit them logically in chunks to recreate the project history.

## Step 1: Initializing the Repository & Core Django Setup
*Purpose: Initialize the empty local git repository and commit the base Django backend skeleton (Step 1).*

**Commands:**
```bash
# 1. Initialize a new local Git repository
git init

# 2. Add the base Django files, configuration, and requirements
git add requirements.txt manage.py .env.example .gitignore
git add config/ apps/__init__.py apps/users/ apps/audit_logs/
git add step_1.md readme-explained.md project-software-specification.md

# 3. Create the first commit representing Step 1
git commit -m "chore: initial commit with Django backend skeleton (Step 1)"
```

## Step 2: ML Integration & Inference Pipeline
*Purpose: Commit the PyTorch inference models, preprocessing pipeline, and load tests.*

**Commands:**
```bash
# Add the ML pipeline, tests, and updated step 2 document
git add ml/ tests/ step_2.md
git commit -m "feat: integrate ResNet18 models and preprocessing pipeline (Step 2)"
```

## Step 3: Inference API Endpoint
*Purpose: Commit the FastAPI application, inference route, and Pydantic schemas.*

```

## Step 4: Database Persistence
*Purpose: Commit the Django models for Uploads and Predictions, admin configurations, and ORM integration in the predict endpoint.*

**Commands:**
```bash
# Add the new Django apps, the step 4 document, the verification test, and this log
git add apps/predictions/ apps/uploads/ step_4.md tests/test_step4.py GitPush.md
git commit -m "feat: implement database persistence using Django ORM (Step 4)"
```
