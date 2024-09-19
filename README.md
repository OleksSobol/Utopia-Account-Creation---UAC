# Utopia API Handler

## Overview
This Python application is a Flask-based API handler that processes requests from Utopia and PowerCode systems. It listens for API callbacks, processes customer data, and interacts with Utopia and PowerCode to create customer accounts and add service plans. The application also sends notification emails regarding the status of customer creation and handles PDF contract downloads.

## Features
- Processes API callbacks from Utopia.
- Searches for customers in Utopia and PowerCode.
- Creates new customer accounts in PowerCode when needed.
- Adds service plans to PowerCode customer accounts.
- Sends notification emails to specified recipients.
- Downloads and attaches PDF contracts to emails.
- Logs all interactions and errors for tracking.

## Technologies Used
- **Flask**: A lightweight web framework for handling HTTP requests.
- **Flask-Mail**: For sending email notifications.
- **Requests**: To interact with external APIs.
- **Logging**: For logging events and errors.
- **Utopia & PowerCode APIs**: External systems integrated for customer and service management.

## Installation

### Prerequisites
- Python 3.x
- Pip (Python package manager)
- `requests`, `flask`, and `flask_mail` libraries. Install them using:



# Changelog

All notable changes to this project will be documented in this file.
## [0.0.4] - 09-17-2024

### Added
- uploaded project to GitHub

## [0.0.3] - 2024-01-20

### Added
- added site_id from Utopia as external_id to powercode customer

## [0.0.2] - 2023-07-10

### Added

- Whole project

## [0.0.1] - 2023-*-*

### Added

- This CHANGELOG file to hopefully serve as an evolving example of a
  standardized open source project CHANGELOG.
