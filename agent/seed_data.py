"""ChromaDB seed data — curated topic-to-verse mappings for semantic search.

When a user asks an abstract question ("I feel lost", "What about forgiveness?"),
the Verse Finder first queries ChromaDB with the topic, then does a deterministic
API.Bible lookup for the exact text of the matched verses.

Each entry has:
  - topic: short theme label
  - description: expanded natural-language description (used as the document
    that gets embedded by ChromaDB's default model)
  - verses: list of API.Bible passage-ID strings
"""

SEED_DATA: list[dict] = [
    # ── Salvation & Grace ──
    {
        "topic": "salvation",
        "description": "Salvation through faith in Jesus Christ, being saved by grace not works",
        "verses": ["EPH.2.8-EPH.2.9", "ROM.10.9", "JHN.3.16-JHN.3.17", "ACT.4.12"],
    },
    {
        "topic": "grace",
        "description": "God's unmerited favour and grace towards sinners",
        "verses": ["EPH.2.8-EPH.2.9", "ROM.5.8", "TIT.2.11", "2CO.12.9"],
    },
    {
        "topic": "born again",
        "description": "Being born again, spiritual rebirth and regeneration",
        "verses": ["JHN.3.3-JHN.3.7", "1PE.1.23", "2CO.5.17", "TIT.3.5"],
    },

    # ── Love ──
    {
        "topic": "love",
        "description": "God's love for humanity, loving one another, the greatest commandment",
        "verses": ["1CO.13.4-1CO.13.8", "JHN.3.16", "1JN.4.8", "ROM.8.38-ROM.8.39"],
    },
    {
        "topic": "love your neighbour",
        "description": "Loving your neighbour as yourself, the second greatest commandment",
        "verses": ["MAT.22.37-MAT.22.39", "LEV.19.18", "GAL.5.14", "ROM.13.10"],
    },
    {
        "topic": "God's love",
        "description": "The depth and breadth of God's unconditional love",
        "verses": ["ROM.5.8", "JHN.3.16", "1JN.4.9-1JN.4.10", "PSA.136.1"],
    },

    # ── Forgiveness ──
    {
        "topic": "forgiveness",
        "description": "Forgiving others, receiving God's forgiveness for sins",
        "verses": ["EPH.4.32", "COL.3.13", "MAT.6.14-MAT.6.15", "1JN.1.9"],
    },
    {
        "topic": "repentance",
        "description": "Turning away from sin, repenting and seeking God",
        "verses": ["ACT.3.19", "2CH.7.14", "ACT.2.38", "LUK.15.7"],
    },

    # ── Hope & Comfort ──
    {
        "topic": "hope",
        "description": "Finding hope in God during difficult times, hope for the future",
        "verses": ["JER.29.11", "ROM.15.13", "ROM.8.28", "PSA.42.11"],
    },
    {
        "topic": "feeling lost",
        "description": "Feeling lost, alone, without direction, needing God's guidance",
        "verses": ["PSA.23.1-PSA.23.6", "ISA.41.10", "MAT.11.28-MAT.11.30", "PSA.46.1"],
    },
    {
        "topic": "comfort in grief",
        "description": "Comfort during bereavement, loss of a loved one, mourning",
        "verses": ["MAT.5.4", "PSA.34.18", "REV.21.4", "2CO.1.3-2CO.1.4"],
    },
    {
        "topic": "anxiety and worry",
        "description": "Overcoming anxiety, worry, and stress through faith",
        "verses": ["PHP.4.6-PHP.4.7", "MAT.6.25-MAT.6.27", "1PE.5.7", "ISA.41.10"],
    },
    {
        "topic": "peace",
        "description": "Finding inner peace, the peace of God that surpasses understanding",
        "verses": ["PHP.4.7", "JHN.14.27", "ISA.26.3", "ROM.5.1"],
    },
    {
        "topic": "depression",
        "description": "Dealing with depression, sadness, despair, feeling crushed in spirit",
        "verses": ["PSA.34.17-PSA.34.18", "PSA.42.11", "ISA.41.10", "MAT.11.28"],
    },
    {
        "topic": "loneliness",
        "description": "Feeling lonely and abandoned, God never leaves us",
        "verses": ["DEU.31.6", "PSA.68.6", "HEB.13.5", "ISA.41.10"],
    },

    # ── Faith & Trust ──
    {
        "topic": "faith",
        "description": "Living by faith, trusting God, the definition of faith",
        "verses": ["HEB.11.1", "HEB.11.6", "ROM.10.17", "2CO.5.7"],
    },
    {
        "topic": "trust in God",
        "description": "Trusting God's plan and timing even when life is hard",
        "verses": ["PRO.3.5-PRO.3.6", "PSA.37.5", "ISA.40.31", "PSA.56.3"],
    },
    {
        "topic": "patience",
        "description": "Patience in trials, waiting on the Lord, endurance",
        "verses": ["JAS.1.2-JAS.1.4", "ROM.12.12", "PSA.27.14", "ISA.40.31"],
    },

    # ── Prayer ──
    {
        "topic": "prayer",
        "description": "How to pray, the power of prayer, prayer life",
        "verses": ["MAT.6.9-MAT.6.13", "PHP.4.6", "1TH.5.16-1TH.5.18", "JAS.5.16"],
    },
    {
        "topic": "unanswered prayer",
        "description": "When prayers seem unanswered, God's timing",
        "verses": ["ISA.55.8-ISA.55.9", "2CO.12.8-2CO.12.9", "PSA.27.14", "ROM.8.28"],
    },

    # ── Sin & Redemption ──
    {
        "topic": "sin",
        "description": "The nature of sin, all have sinned, falling short of God's glory",
        "verses": ["ROM.3.23", "ROM.6.23", "1JN.1.8-1JN.1.9", "ISA.53.6"],
    },
    {
        "topic": "redemption",
        "description": "Redemption through Christ's blood, bought with a price",
        "verses": ["EPH.1.7", "ROM.3.24", "1PE.1.18-1PE.1.19", "GAL.3.13"],
    },
    {
        "topic": "temptation",
        "description": "Resisting temptation, God provides a way out",
        "verses": ["1CO.10.13", "JAS.1.12-JAS.1.14", "HEB.4.15-HEB.4.16", "MAT.26.41"],
    },

    # ── Core Doctrines ──
    {
        "topic": "Trinity",
        "description": "The Holy Trinity, three persons one God, Father Son Holy Spirit",
        "verses": ["MAT.28.19", "2CO.13.14", "JHN.1.1-JHN.1.3", "GEN.1.26"],
    },
    {
        "topic": "resurrection",
        "description": "The resurrection of Jesus Christ, proof of resurrection",
        "verses": ["1CO.15.3-1CO.15.6", "ROM.6.9", "JHN.11.25-JHN.11.26", "MAT.28.5-MAT.28.6"],
    },
    {
        "topic": "Holy Spirit",
        "description": "The role of the Holy Spirit, gifts of the Spirit, fruit of the Spirit",
        "verses": ["GAL.5.22-GAL.5.23", "ACT.1.8", "JHN.14.26", "ROM.8.26"],
    },
    {
        "topic": "creation",
        "description": "God as creator, creation of the world, Genesis creation account",
        "verses": ["GEN.1.1", "PSA.19.1", "JHN.1.3", "COL.1.16"],
    },
    {
        "topic": "second coming",
        "description": "The second coming of Christ, end times, return of Jesus",
        "verses": ["ACT.1.11", "MAT.24.30", "1TH.4.16-1TH.4.17", "REV.22.12"],
    },

    # ── Christian Life ──
    {
        "topic": "baptism",
        "description": "The meaning and importance of baptism in Christianity",
        "verses": ["MAT.28.19", "ACT.2.38", "ROM.6.3-ROM.6.4", "GAL.3.27"],
    },
    {
        "topic": "communion",
        "description": "The Lord's Supper, Eucharist, communion, body and blood of Christ",
        "verses": ["LUK.22.19-LUK.22.20", "1CO.11.23-1CO.11.26", "MAT.26.26-MAT.26.28"],
    },
    {
        "topic": "marriage",
        "description": "Biblical perspective on marriage, husbands and wives",
        "verses": ["GEN.2.24", "EPH.5.25", "EPH.5.22-EPH.5.33", "1CO.13.4-1CO.13.7"],
    },
    {
        "topic": "serving others",
        "description": "Serving others, humility, caring for the poor and needy",
        "verses": ["MAT.25.35-MAT.25.40", "GAL.5.13", "PHP.2.3-PHP.2.4", "MRK.10.45"],
    },
    {
        "topic": "giving and generosity",
        "description": "Tithing, generosity, cheerful giving",
        "verses": ["2CO.9.7", "ACT.20.35", "PRO.11.25", "MAL.3.10"],
    },
    {
        "topic": "wisdom",
        "description": "Seeking wisdom from God, the beginning of wisdom",
        "verses": ["PRO.9.10", "JAS.1.5", "PRO.3.13", "PSA.111.10"],
    },
    {
        "topic": "strength",
        "description": "Finding strength in God, being strong in the Lord",
        "verses": ["PHP.4.13", "ISA.40.31", "2CO.12.9-2CO.12.10", "PSA.46.1"],
    },
    {
        "topic": "obedience",
        "description": "Obedience to God, following God's commandments",
        "verses": ["JHN.14.15", "1SA.15.22", "DEU.11.13", "JAS.1.22"],
    },
    {
        "topic": "purpose",
        "description": "Finding life's purpose, God's purpose for your life",
        "verses": ["JER.29.11", "ROM.8.28", "EPH.2.10", "PRO.16.9"],
    },
    {
        "topic": "suffering",
        "description": "Understanding suffering, why God allows suffering",
        "verses": ["ROM.8.18", "2CO.4.17", "1PE.5.10", "JAS.1.2-JAS.1.4"],
    },
    {
        "topic": "healing",
        "description": "Physical and spiritual healing, God the healer",
        "verses": ["JER.17.14", "PSA.147.3", "ISA.53.5", "JAS.5.14-JAS.5.15"],
    },

    # ── The Bible Itself ──
    {
        "topic": "scripture authority",
        "description": "The authority and inspiration of the Bible, God's word",
        "verses": ["2TI.3.16-2TI.3.17", "HEB.4.12", "PSA.119.105", "ISA.40.8"],
    },

    # ── Controversial / Denomination-Specific ──
    {
        "topic": "deuterocanonical books",
        "description": "Books in the Catholic and Orthodox Bible but not Protestant: Maccabees, Wisdom, Sirach, Tobit, Judith, Baruch",
        "verses": ["SIR.1.1", "WIS.1.1", "1MA.1.1"],  # Note: May not be in KJV on API.Bible
    },
    {
        "topic": "infant baptism",
        "description": "The practice of baptising infants, debated across denominations",
        "verses": ["ACT.16.33", "ACT.2.38-ACT.2.39", "MAT.19.14", "MRK.10.14"],
    },
    {
        "topic": "predestination",
        "description": "Predestination versus free will, election, Calvinism Arminianism debate",
        "verses": ["ROM.8.29-ROM.8.30", "EPH.1.4-EPH.1.5", "2PE.3.9", "JHN.3.16"],
    },
    {
        "topic": "Mary",
        "description": "The role of the Virgin Mary, Marian dogmas, Catholic vs Protestant views",
        "verses": ["LUK.1.28", "LUK.1.46-LUK.1.48", "JHN.2.3-JHN.2.5", "MAT.1.23"],
    },
    {
        "topic": "confession",
        "description": "Sacrament of confession, confessing sins to a priest vs directly to God",
        "verses": ["JAS.5.16", "1JN.1.9", "PSA.32.5", "JHN.20.22-JHN.20.23"],
    },

    # ── Key Figures ──
    {
        "topic": "Jesus identity",
        "description": "Who is Jesus Christ, the Son of God, Messiah, fully God and fully man",
        "verses": ["JHN.1.1", "JHN.1.14", "COL.2.9", "HEB.1.3"],
    },
    {
        "topic": "Ten Commandments",
        "description": "The Ten Commandments, God's law given to Moses",
        "verses": ["EXO.20.1-EXO.20.17", "DEU.5.6-DEU.5.21", "MAT.22.37-MAT.22.40"],
    },
    {
        "topic": "heaven",
        "description": "What heaven is like, eternal life, being with God forever",
        "verses": ["JHN.14.2-JHN.14.3", "REV.21.1-REV.21.4", "PHP.3.20", "1CO.2.9"],
    },
    {
        "topic": "hell",
        "description": "The concept of hell, eternal separation from God, judgment",
        "verses": ["MAT.25.46", "REV.20.15", "MAT.10.28", "2TH.1.9"],
    },
    {
        "topic": "angels",
        "description": "Angels, guardian angels, angelic beings in the Bible",
        "verses": ["HEB.1.14", "PSA.91.11", "HEB.13.2", "MAT.18.10"],
    },
    {
        "topic": "worship",
        "description": "Worshipping God, praise and worship, how to worship",
        "verses": ["JHN.4.24", "PSA.95.6", "ROM.12.1", "PSA.150.1-PSA.150.6"],
    },
    {
        "topic": "gratitude",
        "description": "Being thankful, giving thanks to God in all circumstances",
        "verses": ["1TH.5.18", "PSA.100.4", "COL.3.17", "PHP.4.6"],
    },
    {
        "topic": "justice",
        "description": "God's justice, pursuing justice, caring for the oppressed",
        "verses": ["MIC.6.8", "ISA.1.17", "PSA.82.3", "AMO.5.24"],
    },
    {
        "topic": "mercy",
        "description": "God's mercy, being merciful to others",
        "verses": ["LAM.3.22-LAM.3.23", "LUK.6.36", "MIC.7.18", "EPH.2.4-EPH.2.5"],
    },
    {
        "topic": "fear of the Lord",
        "description": "The fear of the Lord, reverence for God, the beginning of wisdom",
        "verses": ["PRO.9.10", "PSA.111.10", "PRO.1.7", "DEU.10.12"],
    },
]
