# 📝 Technical requirements documentation

[Reference document](https://github.com/alexey-goloburdin/thanks/blob/main/docs/technical_requirements.md)

## 🚀 Goal of the project

To develop the system of sport event planning for any individual or organization interested in setting up their sport activity event. Sport event can be any tournament or competition activity between people or teams. Organizers can create and a sport event and participants will register to it, where organizer will have a dashboard with peoples registered to their sport event and can download clean excel table with registered people and distributed over their grading degree (classes / ages / weights and so on). Additionally system must be responsive with all entities organizers & participants linked by event sent notifications mechanisms (email and telegram). System will be entirely based on traditional web without any mobile app

## ✍️ Description of the project

System is composed out of following functional blocks:
- Registration, authN & authZ
- Organizer's functionality
    - CRUD on event
- Partiticipant's functionality
    - Register to event
    - Refuse from participation
    - Update registration details
    - Subscription on upcoming events
- Notification over email / telegram

## 👥 Types of users

System envisage following main types of users such as:

- Guest (No need for Login, AuthN & AuthZ)
- Organizer
- Participant
- Team (?)
- Attendee (?)

Organier can be a participant, but participant can't be an organizer.

## 🫣 Registration

### Registration fields :: participant 🏃

- First name
- Last name
- Birth date
- Contact details
    1. email (mandatory)
    2. phone number (mandatory)
    3. telegram (optional)
    4. whatsapp (optional)
- Password

### Registration fields :: organizer 🗄️

- Extends everything from participant
- Type: individual / organization
- About organizer

## 🔒 Authentification of users

Authentication is entirely done once off password provided over email or url?

## 👽 Functionality for users

First open