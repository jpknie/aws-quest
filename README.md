# AWS Quest

**AWS Quest** is an experimental roguelike game built around learning Amazon Web Services.

Instead of grinding through another list of multiple-choice questions, the idea is to turn AWS knowledge into part of a dungeon-crawling game: explore procedurally generated levels, encounter challenges, survive the dungeon — and answer AWS questions along the way.

The project started as a combination of two things I wanted to experiment with: building a roguelike from scratch and studying AWS in a slightly less boring way.

## The Idea

AWS Quest combines traditional roguelike mechanics with AWS-related questions and challenges.

The goal is to make learning part of the gameplay rather than building a conventional quiz application with a game-themed UI around it.

The game is being developed iteratively, with mechanics and AWS learning features added as the project evolves.

## Current Features

The project currently includes or experiments with:

- Procedurally generated dungeon layouts
- BSP-based room generation
- Player movement and exploration
- Camera and viewport handling
- Lighting and visibility
- Basic roguelike game architecture
- AWS questions integrated into the game

More traditional roguelike mechanics such as items, enemies, collisions and progression can be added as the project develops.

## AWS Learning

The AWS content is intended to cover topics encountered while studying AWS, including areas such as:

- Compute
- Storage
- Networking
- Databases
- Security and IAM
- Monitoring and observability
- High availability and scalability
- AWS pricing and cost management
- Cloud architecture concepts

The initial focus is AWS Cloud Practitioner level knowledge, but the game architecture is not intended to be tied to a single certification.

## Tech

The project is currently built with:

- Python
- Pygame
- Procedural generation
- Binary Space Partitioning (BSP)

Part of the purpose of the project is simply experimentation: trying different approaches to procedural generation, game architecture and gameplay while turning AWS study material into something interactive.

## Why?

Because apparently answering AWS practice questions normally wasn't complicated enough.

So I made a dungeon.

## Status

🚧 **Work in progress**

AWS Quest is a personal learning and experimentation project. Expect unfinished mechanics, questionable architectural decisions, monsters, refactoring and probably more AWS services than any dungeon reasonably needs.

## Running the Project

Clone the repository:

```bash
git clone <repository-url>
cd aws-quest
```

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the game:

```bash
python main.py
```

The exact setup may change as the project evolves.

## License

This project is intended primarily for learning and experimentation.

AWS and Amazon Web Services are trademarks of Amazon.com, Inc. or its affiliates. This project is not affiliated with or endorsed by Amazon Web Services.
