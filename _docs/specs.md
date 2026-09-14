# ChopTheBill – Specs

## 🎯 Scope
A web application for tracking and managing shared expenses across groups.  
Focus: **tracking balances only** (no payment integration).

## 🛠 Tech Stack
- **Frontend**: React  
- **Backend**: FastAPI  
- **Database**: SQLite  
- **Deployment**: Web application  

## 🔑 MVP Features
1. **Add & Track Expenses**  
   - Log expenses with descriptions, payer, amount, and custom splits (unequal shares supported).  
2. **Balance Calculation**  
   - Automatically compute net balances and minimize transactions across the group.  
3. **Group Management**  
   - Create groups (friends, roommates, trips) and organize expenses per group.  

## 🚀 Non-MVP Features (Future Enhancements)
- **Expense Categories** (Food, Travel, Utilities) with filtering.  
- **Export Reports** (CSV/PDF summaries of expenses and balances).  
- **Notifications** (email reminders for unsettled balances).  
- **Multi-Currency Support** for international groups.  
- **Admin Controls** (group owner can edit/remove expenses).  

## 👥 Authentication
- User signup/login required.  
- Basic session management for secure access.  
- Password hashing and JWT-based authentication.  

## 📊 Data Model
- **User**: id, name, email, password_hash  
- **Group**: id, name, members (User ids)  
- **Expense**: id, group_id, description, amount, payer_id, date  
- **Split**: id, expense_id, user_id, share_amount  

## 🔄 User Flow
1. **Create Group** → Add members.  
2. **Add Expense** → Enter payer, amount, description, and split details.  
3. **View Balances** → Dashboard shows minimized transactions (who owes whom).  

## 🎨 UI Design
- **Login/Signup Page** → Simple form with email & password.  
- **Dashboard** → List of groups, option to create new group.  
- **Group Page** →  
  - Expense list (table with description, payer, amount, date).  
  - “Add Expense” button → modal form for new expense.  
  - Balance summary → clear list of who owes whom.  
- **Navigation Bar** → Home, Groups, Profile, Logout.  

## 🔗 Frontend–Backend Interactions
- **Authentication**  
  - `POST /signup` → create new user  
  - `POST /login` → authenticate and return JWT  
- **Groups**  
  - `POST /groups` → create group  
  - `GET /groups` → list user’s groups  
- **Expenses**  
  - `POST /expenses/{group_id}` → add expense with splits  
  - `GET /expenses/{group_id}` → list expenses in group  
- **Balances**  
  - `GET /balances/{group_id}` → compute and return minimized transactions  

## ⚙️ Non-Functional Requirements
- **Performance**: Handle groups up to ~50 members smoothly.  
- **Scalability**: SQLite for MVP, but design should allow migration to Postgres/MySQL later.  
- **Security**: Password hashing, JWT authentication, input validation, role-based access.  
- **Usability**: Simple, intuitive UI with clear balances and expense history.  

## 📑 API Contract (OpenAPI-style)
- **Authentication**: `/signup`, `/login`  
- **Groups**: `/groups` (GET, POST)  
- **Expenses**: `/expenses/{group_id}` (GET, POST)  
- **Balances**: `/balances/{group_id}` (GET)  
- **Schemas**: User, Group, Expense, Split, Balance  
- **Security**: Bearer JWT tokens  

