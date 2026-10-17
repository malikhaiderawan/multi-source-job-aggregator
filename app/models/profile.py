import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class WorkExperience(BaseModel):
    company: str
    role: str
    period: str
    highlights: List[str]

class FeaturedProject(BaseModel):
    title: str
    stack: List[str]
    description: str
    platforms: List[str]

class CandidateProfile(BaseModel):
    name: str = "Anser Nawaz"
    headline: str = "Senior Full Stack & Mobile Engineer | Team Lead (6+ Years Experience)"
    email: str = Field(default_factory=lambda: os.getenv("CANDIDATE_EMAIL", "ansernawaz786@gmail.com"))
    phone: str = Field(default_factory=lambda: os.getenv("CANDIDATE_PHONE", "+92 305 4100126"))
    location: str = "Lahore, Pakistan"
    github: str = "https://github.com/Anser786"
    linkedin: str = "https://linkedin.com/in/ansernawaz"
    total_years_experience: float = 6.0
    
    categories: Dict[str, List[str]] = {
        "Mobile": [
            "React Native", "Flutter", "iOS", "Android", "Cross-Platform",
            "Android Native", "iOS / Xcode", "Mobile Architecture", "Redux", "Mobile UI"
        ],
        "Frontend": [
            "React.js", "React", "Next.js", "TypeScript", "JavaScript",
            "HTML/CSS", "Tailwind CSS", "Redux", "Websites", "Dashboards", "E-commerce"
        ],
        "Backend": [
            "Node.js", "Express.js", "REST APIs", "Socket.io", "WebSockets",
            "Authentication", "JWT", "API Integrations", "Microservices"
        ],
        "Full-stack": [
            "Full Stack", "SaaS", "Databases", "MySQL", "Firebase",
            "Docker", "Cloud Deployment", "Senior Software Engineer", "Technical Leadership", "Architecture"
        ]
    }
    
    all_skills: List[str] = [
        "React Native", "Flutter", "React.js", "Next.js", "Node.js", "Express.js",
        "TypeScript", "JavaScript", "REST APIs", "Socket.io", "MySQL", "Firebase",
        "Docker", "Git", "Redux", "iOS", "Android", "Tailwind CSS", "CI/CD",
        "Code Reviews", "System Architecture", "Team Leadership"
    ]

    target_locations: List[str] = [
        "Lahore", "Pakistan", "Islamabad", "Karachi",
        "Remote", "Worldwide", "Anywhere", "Global", "EMEA", "APAC", "US"
    ]

    work_history: List[WorkExperience] = [
        WorkExperience(
            company="ASOFT",
            role="Senior Full-Stack & Mobile Developer (Freelance)",
            period="Jan 2024 - Present",
            highlights=[
                "Architecting high-scale cross-platform mobile and web applications using React Native, Next.js, and Node.js.",
                "Engineering robust RESTful APIs, microservices, and real-time synchronization pipelines.",
                "Delivering end-to-end full-stack solutions for international clients and SaaS platforms."
            ]
        ),
        WorkExperience(
            company="Coder Crew",
            role="Team Lead of App Development",
            period="Jun 2023 - Jan 2024",
            highlights=[
                "Led an engineering team of mobile and web developers delivering mission-critical applications.",
                "Governed system architecture, technical roadmaps, rigorous code reviews, and quality standards.",
                "Liaised directly with clients to translate complex product specifications into production-ready software."
            ]
        ),
        WorkExperience(
            company="NthLogics",
            role="Frontend App Developer",
            period="Apr 2022 - Jun 2023",
            highlights=[
                "Architected and built the Blockonaire gaming platform from scratch.",
                "Engineered responsive, high-performance UIs using React.js and modern state management.",
                "Integrated secure blockchain transactions and web3 decentralized services."
            ]
        ),
        WorkExperience(
            company="TectSoft",
            role="Full Stack App Developer",
            period="Oct 2020 - Mar 2022",
            highlights=[
                "Engineered full-stack web and mobile apps using React, Node.js, and MySQL.",
                "Designed and implemented secure RESTful APIs with JWT authentication.",
                "Developed low-latency real-time chat and notification capabilities using Socket.io."
            ]
        )
    ]

    featured_projects: List[FeaturedProject] = [
        FeaturedProject(
            title="Fofo",
            stack=["React Native", "Node.js", "REST APIs"],
            description="High-engagement social application for discovering, bookmarking, and organizing multimedia content (Instagram Reels, TikToks, articles).",
            platforms=["iOS", "Android"]
        ),
        FeaturedProject(
            title="AfroTech Connect",
            stack=["React Native", "Node.js", "Firebase", "WebSockets"],
            description="Official conference companion platform for AfroTech, enabling real-time attendee networking, event scheduling, and community engagement.",
            platforms=["iOS", "Android", "Web"]
        ),
        FeaturedProject(
            title="KNO",
            stack=["React Native", "Node.js", "Firebase"],
            description="Contact and professional relationship management solution streamlining network communication and outreach.",
            platforms=["Android"]
        ),
        FeaturedProject(
            title="Blockonaire",
            stack=["React.js", "TypeScript", "Web3", "Tailwind CSS"],
            description="Interactive blockchain-based gaming and play-to-earn platform engineered with custom React interfaces.",
            platforms=["Web"]
        )
    ]

ANSER_PROFILE = CandidateProfile()
