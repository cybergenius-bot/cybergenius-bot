# Overview

КиберГений is a Russian-language Telegram Q&A bot that provides categorized advice and responses to user questions. The bot operates on a freemium model where users get 2 free questions and then pay per category based on pricing tiers (ranging from 10-30 ₪). It covers six main categories: Construction (Стройка), Relationships (Отношения), Business (Бизнес), Life (Жизнь), Sex (Секс), and Other (Другое).

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **aiogram**: Asynchronous Python framework for Telegram Bot API
- **Architecture Pattern**: Event-driven message handling with dispatcher pattern
- **State Management**: In-memory user session storage (suitable for development, needs database for production)

## Message Flow
- **Menu System**: Hierarchical keyboard-based navigation with category selection
- **Response Generation**: Template-based smart responses tailored to each category
- **User Tracking**: Session-based tracking of free question limits and selected categories

## Application Structure
- **bot.py**: Core bot logic, message handlers, and user interface
- **config.py**: Configuration management with environment variables and category definitions
- **main.py**: Application entry point with health check endpoints and bot lifecycle management

## Deployment Architecture
- **Multi-threaded**: Bot runs in separate thread alongside web server
- **Health Monitoring**: HTTP endpoints for service health checks and bot status
- **Async/Await**: Leverages Python's asyncio for concurrent message handling

## User Data Management
- **In-Memory Storage**: Current implementation uses Python dictionaries for user session data
- **Data Structure**: Tracks free question count, selected category, and total questions per user
- **Session Persistence**: Data persists only during application runtime

# External Dependencies

## Core Dependencies
- **aiogram**: Telegram Bot API framework for Python
- **aiohttp**: Asynchronous HTTP client/server framework for health check endpoints
- **asyncio**: Python's built-in asynchronous programming library

## Telegram Integration
- **Telegram Bot API**: Primary interface for message handling and user interaction
- **Bot Token**: Environment variable-based authentication with fallback hardcoded token

## Configuration Management
- **Environment Variables**: TELEGRAM_BOT_TOKEN for secure token storage
- **Static Configuration**: Category pricing, free question limits, and response templates

## Future Considerations
- **Database Integration**: Current in-memory storage should be replaced with persistent database (PostgreSQL recommended)
- **Payment Processing**: Payment gateway integration needed for premium features
- **Analytics**: User behavior tracking and question categorization analytics