{
  "syllabus": {
    "syllabus_code": "2210",
    "level": "O Level",
    "title": "Cambridge O Level Computer Science",
    "years": ["2026", "2027", "2028"],
    "topics": [
      {
        "topic_number": "1",
        "topic_name": "Data representation",
        "sub_topics": [
          {
            "sub_topic_number": "1.1",
            "sub_topic_name": "Number systems",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand how and why computers use binary to represent all forms of data.",
                "notes_and_guidance": "Data needs to be converted to binary for processing. Data is processed using logic gates and stored in registers."
              },
              {
                "objective_number": "2",
                "description": [
                  "(a) Understand denary, binary, and hexadecimal number systems.",
                  "(b) Convert between (i) positive denary and positive binary, (ii) positive denary and positive hexadecimal, (iii) positive hexadecimal and positive binary."
                ],
                "notes_and_guidance": "Denary is base 10, binary is base 2, and hexadecimal is base 16. Only integer values are used. Conversions in both directions (e.g. denary to binary and vice versa) with a maximum of 16 bits for binary numbers."
              },
              {
                "objective_number": "3",
                "description": "Understand how and why hexadecimal is a beneficial method of data representation.",
                "notes_and_guidance": "Hexadecimal is used in computer science areas for its shorter representation compared to binary and easier human understanding."
              },
              {
                "objective_number": "4",
                "description": [
                  "(a) Add two positive 8-bit binary integers.",
                  "(b) Understand overflow and why it occurs in binary addition."
                ],
                "notes_and_guidance": "Overflow occurs if the result exceeds 255 for 8 bits. Computers have fixed register sizes (e.g. 16-bit). Overflow happens when the result exceeds the maximum representable value."
              },
              {
                "objective_number": "5",
                "description": "Perform logical binary shifts on positive 8-bit binary integers and understand the effect.",
                "notes_and_guidance": "Includes logical left and right shifts, and multiple shifts. Lost bits are discarded, zeros are added at the opposite end. Shifts multiply or divide the value. Most or least significant bits are lost."
              },
              {
                "objective_number": "6",
                "description": "Use two's complement to represent positive and negative 8-bit binary integers.",
                "notes_and_guidance": "Convert between binary or denary integers (positive and negative) and their two's complement 8-bit representation."
              }
            ]
          },
          {
            "sub_topic_number": "1.2",
            "sub_topic_name": "Text, sound and images",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand how text is represented and the use of character sets, including ASCII and Unicode.",
                "notes_and_guidance": "Text is converted to binary for processing. Unicode supports a larger range of characters (including languages and emojis) than ASCII. Unicode requires more bits per character."
              },
              {
                "objective_number": "2",
                "description": "Understand computer representation of sound, including sample rate and sample resolution.",
                "notes_and_guidance": "Sound is sampled and converted to binary. Sample rate is number of samples per second, resolution is the bits per sample. Higher values increase accuracy and file size."
              },
              {
                "objective_number": "3",
                "description": "Understand computer representation of images, including resolution and colour depth.",
                "notes_and_guidance": "An image is a grid of pixels stored in binary. Resolution is pixel count; colour depth is bits per pixel. Higher values improve size and quality."
              }
            ]
          },
          {
            "sub_topic_number": "1.3",
            "sub_topic_name": "Data storage and compression",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand how data storage is measured.",
                "notes_and_guidance": "Units: bit, nibble, byte, kibibyte (KiB), mebibyte (MiB), gibibyte (GiB), tebibyte (TiB), pebibyte (PiB), exbibyte (EiB). Conversion factors: 8 bits in a byte, 1024 units in the next size up."
              },
              {
                "objective_number": "2",
                "description": "Calculate the file size of image and sound files.",
                "notes_and_guidance": "Give answers in specified units. Use 1024-based conversion. Input data may include resolution, colour depth, sample rate, bit depth, and duration."
              },
              {
                "objective_number": "3",
                "description": "Understand the purpose and need for data compression.",
                "notes_and_guidance": "Compression reduces file size, saving bandwidth, storage, and transmission time."
              },
              {
                "objective_number": "4",
                "description": "Understand lossy and lossless compression methods.",
                "notes_and_guidance": "Lossy removes data permanently (e.g. lowering resolution/sample rate). Lossless compresses without losing information (e.g. run length encoding)."
              }
            ]
          }
        ]
      },
      {
        "topic_number": "2",
        "topic_name": "Data transmission",
        "sub_topics": [
          {
            "sub_topic_number": "2.1",
            "sub_topic_name": "Types and methods of data transmission",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": [
                  "(a) Understand that data is split into packets for transmission.",
                  "(b) Describe the structure of a packet.",
                  "(c) Describe packet switching."
                ],
                "notes_and_guidance": "Packets contain a header, payload, and trailer. Headers include destination, source addresses, and packet number. Packets may follow different routes, can arrive out of order, and are reassembled on arrival."
              },
              {
                "objective_number": "2",
                "description": [
                  "(a) Describe data transmission methods.",
                  "(b) Explain suitability of each method in different scenarios."
                ],
                "notes_and_guidance": "Methods include: serial, parallel, simplex, half-duplex, full-duplex. Advantages and disadvantages should be compared."
              },
              {
                "objective_number": "3",
                "description": "Understand USB interface for data transmission.",
                "notes_and_guidance": "Includes USB benefits and drawbacks."
              }
            ]
          },
          {
            "sub_topic_number": "2.2",
            "sub_topic_name": "Methods of error detection",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand the need to check for errors after data transmission and how errors can occur.",
                "notes_and_guidance": "Errors may result from interference (data loss, gain, or change)."
              },
              {
                "objective_number": "2",
                "description": "Describe error detection: parity check (odd/even), checksum, and echo check.",
                "notes_and_guidance": "Includes parity byte and parity block check."
              },
              {
                "objective_number": "3",
                "description": "Describe use of check digits to detect data entry errors and give examples such as ISBN and bar codes.",
                "notes_and_guidance": "Check digits help detect errors in manual data entry (e.g. ISBN, bar codes)."
              },
              {
                "objective_number": "4",
                "description": "Describe ARQ (Automatic Repeat Query) to establish error-free data receipt.",
                "notes_and_guidance": "Includes positive/negative acknowledgements and timeouts."
              }
            ]
          },
          {
            "sub_topic_number": "2.3",
            "sub_topic_name": "Encryption",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand the purpose of encryption when transmitting data.",
                "notes_and_guidance": "Encryption protects data during transmission."
              },
              {
                "objective_number": "2",
                "description": "Understand symmetric and asymmetric encryption.",
                "notes_and_guidance": "Asymmetric encryption uses public and private keys."
              }
            ]
          }
        ]
      },
      {
        "topic_number": "3",
        "topic_name": "Hardware",
        "sub_topics": [
          {
            "sub_topic_number": "3.1",
            "sub_topic_name": "Computer architecture",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": [
                  "(a) Understand the CPU's role in a computer.",
                  "(b) Understand what is meant by a microprocessor."
                ],
                "notes_and_guidance": "The CPU processes instructions and data. A microprocessor is an integrated circuit on a single chip."
              },
              {
                "objective_number": "2",
                "description": [
                  "(a) Understand the purpose of CPU components in a Von Neumann architecture.",
                  "(b) Describe the fetch-decode-execute (FDE) cycle, including each component's role."
                ],
                "notes_and_guidance": "Covers ALU, CU, registers (PC, MAR, MDR, CIR, ACC), buses (address, data, control). Details how data/instructions are fetched from RAM, processed, stored in registers, and executed using buses and units."
              },
              {
                "objective_number": "3",
                "description": "Understand core, cache, and clock in a CPU and their effect on performance.",
                "notes_and_guidance": "CPU performance depends on number of cores, cache size, and clock speed."
              },
              {
                "objective_number": "4",
                "description": "Understand the purpose and use of a CPU instruction set.",
                "notes_and_guidance": "An instruction set lists all machine code commands a CPU can process."
              },
              {
                "objective_number": "5",
                "description": "Describe embedded systems, their characteristics, and devices in which they are used.",
                "notes_and_guidance": "Embedded systems perform dedicated functions (e.g., appliances, cars, security, vending). They differ from general-purpose computers (e.g., PCs, laptops)."
              }
            ]
          },
          {
            "sub_topic_number": "3.2",
            "sub_topic_name": "Input and output devices",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand what an input device is and why it is used.",
                "notes_and_guidance": "Examples: barcode scanner, digital camera, keyboard, microphone, optical mouse, QR scanner, touch screens (resistive/capacitive/infra-red), 2D/3D scanners."
              },
              {
                "objective_number": "2",
                "description": "Understand what an output device is and why it is used.",
                "notes_and_guidance": "Examples: actuator, DLP projector, inkjet/laser printer, LED/LCD screen/projector, speaker, 3D printer."
              },
              {
                "objective_number": "3",
                "description": [
                  "(a) Understand sensors and their purposes.",
                  "(b) Identify data captured and suitable scenario for each sensor."
                ],
                "notes_and_guidance": "Types: acoustic, accelerometer, flow, gas, humidity, infra-red, level, light, magnetic field, moisture, pH, pressure, proximity, temperature."
              }
            ]
          },
          {
            "sub_topic_number": "3.3",
            "sub_topic_name": "Data storage",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand primary storage.",
                "notes_and_guidance": "Primary storage (RAM/ROM) is directly accessed by CPU. Know why both are needed and their differences."
              },
              {
                "objective_number": "2",
                "description": "Understand secondary storage.",
                "notes_and_guidance": "Secondary storage is not accessed directly by CPU and is needed for permanent data storage."
              },
              {
                "objective_number": "3",
                "description": "Describe magnetic, optical, and solid-state storage operations and give examples.",
                "notes_and_guidance": "Magnetic: platters, tracks, sectors, electromagnets (HDD). Optical: lasers, pits/lands (CD, DVD, Blu-ray). Solid-state: NAND/NOR, transistors as control/floating gates (SSD, SD card, USB drive)."
              },
              {
                "objective_number": "4",
                "description": "Describe virtual memory and why it is needed.",
                "notes_and_guidance": "Pages are transferred between RAM and virtual memory as needed."
              },
              {
                "objective_number": "5",
                "description": "Understand cloud storage.",
                "notes_and_guidance": "Cloud storage is accessed remotely unlike local storage."
              },
              {
                "objective_number": "6",
                "description": "Explain advantages/disadvantages of cloud vs. local storage.",
                "notes_and_guidance": "Cloud storage requires physical servers for data."
              }
            ]
          },
          {
            "sub_topic_number": "3.4",
            "sub_topic_name": "Network hardware",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand that a network interface card (NIC) is needed to access a network.",
                "notes_and_guidance": "A NIC is required for a device to connect to a network."
              },
              {
                "objective_number": "2",
                "description": "Understand the purpose and structure of a MAC address.",
                "notes_and_guidance": "NICs are assigned a MAC address during manufacture. MAC addresses use hexadecimal and have manufacturer and serial codes."
              },
              {
                "objective_number": "3",
                "description": [
                  "(a) Understand the purpose of an Internet Protocol (IP) address.",
                  "(b) Know different types of IP addresses."
                ],
                "notes_and_guidance": "IP addresses can be static or dynamic. Understand characteristics/differences between IPv4 and IPv6."
              },
              {
                "objective_number": "4",
                "description": "Describe the role of a router in a network.",
                "notes_and_guidance": "A router sends data to a destination, can assign IP addresses, and connects local networks to the Internet."
              }
            ]
          }
        ]
      },
      {
        "topic_number": "4",
        "topic_name": "Software",
        "sub_topics": [
          {
            "sub_topic_number": "4.1",
            "sub_topic_name": "Types of software and interrupts",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Describe the difference between system and application software; provide examples.",
                "notes_and_guidance": "System software: services for computer (OS, utilities). Application software: services for user."
              },
              {
                "objective_number": "2",
                "description": "Describe the role and functions of an operating system.",
                "notes_and_guidance": "Includes file management, interrupt handling, interface provision, peripheral/driver/memory management, multitasking, application platform, security, user account management."
              },
              {
                "objective_number": "3",
                "description": "Understand how hardware, firmware, and operating system are required to run application software.",
                "notes_and_guidance": "Apps run on the OS; OS runs on firmware; firmware (bootloader) runs on hardware."
              },
              {
                "objective_number": "4",
                "description": "Describe the role and operation of interrupts.",
                "notes_and_guidance": "Covers generation and handling via interrupt service routine. Examples: division by zero, memory access conflict (software); key press, mouse movement (hardware)."
              }
            ]
          },
          {
            "sub_topic_number": "4.2",
            "sub_topic_name": "Types of programming language, translators and IDEs",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Explain high-level vs. low-level languages, with advantages and disadvantages.",
                "notes_and_guidance": "Covers readability, debugging ease, machine independence, hardware interaction."
              },
              {
                "objective_number": "2",
                "description": "Understand that assembly language uses mnemonics and requires an assembler for translation.",
                "notes_and_guidance": "Assembly language is a form of low-level language using mnemonics."
              },
              {
                "objective_number": "3",
                "description": "Describe compiler and interpreter operation: how each translates high-level language and reports errors.",
                "notes_and_guidance": "Compiler translates all code before execution, produces executable. Interpreter translates and executes line-by-line, stops at errors. Compiler gives error report for entire code; interpreter stops at first error."
              },
              {
                "objective_number": "4",
                "description": "Explain the advantages and disadvantages of compilers and interpreters.",
                "notes_and_guidance": "Interpreters are mainly for program development, compilers for translating final programs."
              },
              {
                "objective_number": "5",
                "description": "Explain the role and functions of an IDE.",
                "notes_and_guidance": "Functions include code editor, run-time environment, translators, error diagnostics, auto-completion, auto-correction, pretty print."
              }
            ]
          }
        ]
      },
      {
        "topic_number": "5",
        "topic_name": "The internet and its uses",
        "sub_topics": [
          {
            "sub_topic_number": "5.1",
            "sub_topic_name": "The internet and the world wide web",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand the difference between the internet and the World Wide Web.",
                "notes_and_guidance": "The internet is the infrastructure. The World Wide Web is the collection of websites and web pages accessed through the internet."
              },
              {
                "objective_number": "2",
                "description": "Understand what a Uniform Resource Locator (URL) is.",
                "notes_and_guidance": "A URL is a text address for a web page; it can include protocol, domain name, and page or file name."
              },
              {
                "objective_number": "3",
                "description": "Describe the purpose and operation of HTTP and HTTPS.",
                "notes_and_guidance": "HTTP is used for web page communication; HTTPS adds security with encryption."
              },
              {
                "objective_number": "4",
                "description": "Explain the purpose and functions of a web browser.",
                "notes_and_guidance": "Browsers render HTML to display web pages; features: bookmarks/favourites, history, tabs, cookies, navigation, address bar."
              },
              {
                "objective_number": "5",
                "description": "Describe how web pages are located, retrieved, and displayed when a user enters a URL.",
                "notes_and_guidance": "Roles: web browser, IP address, domain name server (DNS), web server, HTML."
              },
              {
                "objective_number": "6",
                "description": "Explain what cookies are and how they are used (session and persistent cookies).",
                "notes_and_guidance": "Cookies are used for saving personal details, tracking preferences, shopping carts, and login information."
              }
            ]
          },
          {
            "sub_topic_number": "5.2",
            "sub_topic_name": "Digital currency",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand what digital currency is and how it is used.",
                "notes_and_guidance": "Digital currency exists electronically only."
              },
              {
                "objective_number": "2",
                "description": "Understand blockchain for tracking digital currency transactions.",
                "notes_and_guidance": "Blockchain is a digital ledger: a time-stamped, unalterable series of records."
              }
            ]
          },
          {
            "sub_topic_number": "5.3",
            "sub_topic_name": "Cyber security",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Describe the processes and aims of carrying out various cyber security threats.",
                "notes_and_guidance": "Includes brute-force attack, data interception, DDoS, hacking, malware (virus, worm, Trojan, spyware, adware, ransomware), pharming, phishing, social engineering."
              },
              {
                "objective_number": "2",
                "description": "Explain how solutions help keep data safe from security threats.",
                "notes_and_guidance": "Includes access levels, anti-malware (anti-virus, anti-spyware), authentication (password, biometrics, two-step verification), automated updates, checking communications and URLs, firewalls, privacy settings, proxies, SSL."
              }
            ]
          }
        ]
      },
      {
        "topic_number": "6",
        "topic_name": "Automated and emerging technologies",
        "sub_topics": [
          {
            "sub_topic_number": "6.1",
            "sub_topic_name": "Automated systems",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Describe how sensors, microprocessors, and actuators collaborate in automated systems.",
                "notes_and_guidance": "Automated systems involve sensors gathering data, microprocessors processing, and actuators carrying out actions."
              },
              {
                "objective_number": "2",
                "description": "Describe advantages/disadvantages of automated systems for different scenarios.",
                "notes_and_guidance": "Scenarios: industry, transport, agriculture, weather, gaming, lighting, science."
              }
            ]
          },
          {
            "sub_topic_number": "6.2",
            "sub_topic_name": "Robotics",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand what robotics is.",
                "notes_and_guidance": "Robotics is the design, construction, and operation of robots. Examples: factory equipment, domestic robots, drones."
              },
              {
                "objective_number": "2",
                "description": "Describe robot characteristics.",
                "notes_and_guidance": "A robot has a mechanical structure, electronic components (sensors, microprocessors, actuators), and is programmable."
              },
              {
                "objective_number": "3",
                "description": "Understand robot roles and explain their advantages/disadvantages.",
                "notes_and_guidance": "Areas: industry, transport, agriculture, medicine, home, entertainment."
              }
            ]
          },
          {
            "sub_topic_number": "6.3",
            "sub_topic_name": "Artificial intelligence",
            "learning_objectives": [
              {
                "objective_number": "1",
                "description": "Understand what artificial intelligence (AI) means.",
                "notes_and_guidance": "AI is the simulation of intelligent behaviour by computers."
              },
              {
                "objective_number": "2",
                "description": "Describe the main characteristics of AI: data collection, rules for use, reasoning, learning, and adaptation.",
                "notes_and_guidance": "AI can use data, apply rules, reason, and learn/adapt."
              },
              {
                "objective_number": "3",
                "description": "Explain the operation and components of AI systems simulating intelligent behaviour.",
                "notes_and_guidance": "Covers expert systems (knowledge base, rules, inference engine, interface) and machine learning (programs that adapt and learn)."
              }
            ]
          }
        ]
      }
    ]
  },
  "changes_for_2023_2025_syllabus": {
    "source": "Changes to this syllabus for 2023, 2024 and 2025",
    "syllabus_content_changes": {
      "additions": [
        "Topics added (e.g. robotics, AI, 2D arrays).",
        "A guidance column in the syllabus content.",
        "Assessment section updated with flowchart and logic gate symbols.",
        "Revised pseudocode guide included.",
        "Mathematical requirements added.",
        "Command words list provided."
      ],
      "removals": [
        "Topics such as ethics removed."
      ],
      "structural_and_wording_changes": [
        "Learner attributes updated.",
        "Subject content structure improved for coherence.",
        "Learning objective wording clarified.",
        "Boolean logic assessed in Paper 2.",
        "Learning objectives now numbered."
      ]
    },
    "assessment_changes": {
      "revisions": [
        "Syllabus aims clarified.",
        "Assessment objectives reworded, with analysis/design in AO2.",
        "Paper 1 Theory is now Paper 1 Computer Systems.",
        "Paper 2 is now Paper 2 Algorithms, Programming and Logic.",
        "Both papers weighted at 50%.",
        "Paper 2 now has 75 marks.",
        "Pre-release replaced by an unseen scenario question in Paper 2.",
        "Scenario question is 15 marks and requires an algorithm in pseudocode or program code."
      ]
    }
  }
}
