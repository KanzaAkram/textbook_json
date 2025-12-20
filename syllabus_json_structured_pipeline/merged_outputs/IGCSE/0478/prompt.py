[
  {
    "syllabus_name": "Cambridge IGCSE Computer Science 0478",
    "syllabus_years": "2026, 2027 and 2028",
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
                "objective_number": 1,
                "description": "Understand how and why computers use binary to represent all forms of data",
                "notes_and_guidance": "Any form of data must be converted to binary for processing by a computer. Data is processed using logic gates and stored in registers."
              },
              {
                "objective_number": 2,
                "description": "Understand the denary, binary, and hexadecimal number systems and convert between them",
                "notes_and_guidance": "Denary is base 10, binary is base 2, and hexadecimal is base 16. Integers only. Convert numbers in both directions, e.g., denary to binary or binary to denary. Maximum binary number length is 16 bits."
              },
              {
                "objective_number": 3,
                "description": "Understand how and why hexadecimal is used as a beneficial method of data representation",
                "notes_and_guidance": "Hexadecimal is used in many computer science areas and is easier for humans to understand than binary, providing a shorter representation."
              },
              {
                "objective_number": 4,
                "description": "Add two positive 8-bit binary integers and understand the concept of overflow",
                "notes_and_guidance": "Overflow occurs if the value exceeds 255 in an 8-bit register. When the result is too large for the register, an overflow error occurs."
              },
              {
                "objective_number": 5,
                "description": "Perform a logical binary shift on a positive 8-bit binary integer and understand its effect",
                "notes_and_guidance": "Be able to perform logical left and right shifts, including multiple shifts. Bits shifted out are lost and zeros are shifted in. Shifts effectively multiply or divide the value."
              },
              {
                "objective_number": 6,
                "description": "Use the two's complement number system to represent positive and negative 8-bit binary integers",
                "notes_and_guidance": "Convert between positive/negative binary or denary integers and their two's complement (8-bit) representations."
              }
            ]
          },
          {
            "sub_topic_number": "1.2",
            "sub_topic_name": "Text, sound and images",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand how and why computers represent text and the use of character sets, including ASCII and Unicode",
                "notes_and_guidance": "Text is stored in binary using character sets. Unicode supports more symbols and languages than ASCII but uses more bits per character."
              },
              {
                "objective_number": 2,
                "description": "Understand how and why computers represent sound, including the effects of sample rate and sample resolution",
                "notes_and_guidance": "Sound is sampled and converted to binary. The sample rate refers to samples per second and the resolution is bits per sample. Increasing either improves quality and increases file size."
              },
              {
                "objective_number": 3,
                "description": "Understand how and why computers represent images, including the effects of resolution and colour depth",
                "notes_and_guidance": "Images are stored as pixels in binary. Resolution is the number of pixels. Colour depth is bits per pixel. Both increase quality and file size."
              }
            ]
          },
          {
            "sub_topic_number": "1.3",
            "sub_topic_name": "Data storage and compression",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand how data storage is measured",
                "notes_and_guidance": "Units: bit, nibble, byte, kibibyte (KiB), mebibyte (MiB), gibibyte (GiB), tebibyte (TiB), pebibyte (PiB), exbibyte (EiB). Know the relationships between them, e.g., 8 bits in a byte, 1024 mebibytes in a gibibyte."
              },
              {
                "objective_number": 2,
                "description": "Calculate the file size of an image file and a sound file given relevant information",
                "notes_and_guidance": "Use the units specified in questions. All calculations use 1024 as the measurement base. Information may include image resolution, colour depth, sound sample rate, resolution, and length."
              },
              {
                "objective_number": 3,
                "description": "Understand the purpose and need for data compression",
                "notes_and_guidance": "Compression reduces file size, resulting in less bandwidth and storage needed, and faster transmission."
              },
              {
                "objective_number": 4,
                "description": "Understand how files are compressed using lossy and lossless methods",
                "notes_and_guidance": "Lossy removes data permanently (e.g., reducing resolution; sample rate), lossless does not lose data (e.g., run length encoding/RLE)."
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
                "objective_number": 1,
                "description": "Understand data packets, their structure, and the process of packet switching",
                "notes_and_guidance": "A data packet includes header (with destination, sequence number, source), payload and trailer. Data is split into packets and may arrive out of order; routers direct packet routes."
              },
              {
                "objective_number": 2,
                "description": "Describe different methods of data transmission and their suitability for example scenarios",
                "notes_and_guidance": "Methods include serial, parallel, simplex, half-duplex, full-duplex. Know advantages and disadvantages of each."
              },
              {
                "objective_number": 3,
                "description": "Understand the USB interface and how it transmits data",
                "notes_and_guidance": "Understand the benefits and drawbacks of USB."
              }
            ]
          },
          {
            "sub_topic_number": "2.2",
            "sub_topic_name": "Methods of error detection",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand why errors may occur in data transmission and the need to check for errors",
                "notes_and_guidance": "Transmission errors may occur due to interference (loss, gain, or corruption of data)."
              },
              {
                "objective_number": 2,
                "description": "Describe error detection methods: parity check (odd and even), checksum and echo check",
                "notes_and_guidance": "Including parity byte and parity block check."
              },
              {
                "objective_number": 3,
                "description": "Describe how a check digit is used in error detection, including examples such as ISBNs and barcodes"
              },
              {
                "objective_number": 4,
                "description": "Describe how automatic repeat query (ARQ) can be used to ensure error-free data reception",
                "notes_and_guidance": "Includes use of positive/negative acknowledgements and timeouts."
              }
            ]
          },
          {
            "sub_topic_number": "2.3",
            "sub_topic_name": "Encryption",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand the need for and purpose of encryption when transmitting data"
              },
              {
                "objective_number": 2,
                "description": "Understand how data encryption works using symmetric and asymmetric encryption",
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
                "objective_number": 1,
                "description": "Understand the role of the CPU and what a microprocessor is",
                "notes_and_guidance": "CPU processes instructions and data. A microprocessor is an integrated circuit on a single chip."
              },
              {
                "objective_number": 2,
                "description": "Understand the purpose of CPU components in Von Neumann architecture and describe the fetch-decode-execute (FDE) cycle",
                "notes_and_guidance": "Components: ALU, CU; registers: PC, MAR, MDR, CIR, ACC; buses: address, data, control. Know how FDE cycle works, how registers and buses interact."
              },
              {
                "objective_number": 3,
                "description": "Understand what is meant by a core, cache, and clock in a CPU and their effect on performance",
                "notes_and_guidance": "Performance is influenced by number of cores, cache size, and clock speed."
              },
              {
                "objective_number": 4,
                "description": "Understand the purpose and use of a CPU's instruction set",
                "notes_and_guidance": "An instruction set lists the machine code commands that a CPU can process."
              },
              {
                "objective_number": 5,
                "description": "Describe the purpose and characteristics of embedded systems and where they are used",
                "notes_and_guidance": "Embedded systems perform specific functions (e.g., in appliances, cars, etc). Unlike general purpose computers (e.g., PCs, laptops), which perform many functions."
              }
            ]
          },
          {
            "sub_topic_number": "3.2",
            "sub_topic_name": "Input and output devices",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand what input devices are and why they are required",
                "notes_and_guidance": "Examples: barcode scanner, camera, keyboard, microphone, optical mouse, QR code scanner, touch screens (resistive, capacitive, infra-red), 2D/3D scanners."
              },
              {
                "objective_number": 2,
                "description": "Understand what output devices are and why they are required",
                "notes_and_guidance": "Examples: actuator, DLP projector, inkjet printer, laser printer, LED screen, LCD projector, LCD screen, speaker, 3D printer."
              },
              {
                "objective_number": 3,
                "description": "Understand what is meant by a sensor, its purposes, and the data each sensor captures",
                "notes_and_guidance": "Types: acoustic, accelerometer, flow, gas, humidity, infra-red, level, light, magnetic field, moisture, pH, pressure, proximity, temperature. Know example usage scenarios."
              }
            ]
          },
          {
            "sub_topic_number": "3.3",
            "sub_topic_name": "Data storage",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand what is meant by primary storage",
                "notes_and_guidance": "Primary storage (RAM, ROM) is directly accessed by the CPU. Know why both RAM and ROM are needed and their differences."
              },
              {
                "objective_number": 2,
                "description": "Understand what is meant by secondary storage",
                "notes_and_guidance": "Secondary storage is not directly accessed by the CPU; it stores data more permanently."
              },
              {
                "objective_number": 3,
                "description": "Describe how magnetic, optical, and solid-state (flash) storage work, and examples of each",
                "notes_and_guidance": "Magnetic: platters, tracks, sectors (HDD); optical: lasers read pits/lands (CD, DVD, Blu-ray); solid-state: NAND/NOR tech, transistors as gates (SSD, SD card, USB drive)."
              },
              {
                "objective_number": 4,
                "description": "Describe virtual memory, how it is created, used, and why it is necessary",
                "notes_and_guidance": "Data pages are swapped between RAM and virtual memory as needed."
              },
              {
                "objective_number": 5,
                "description": "Understand what cloud storage is"
              },
              {
                "objective_number": 6,
                "description": "Explain the advantages and disadvantages of cloud storage compared to local storage",
                "notes_and_guidance": "Cloud storage is accessible remotely, but requires physical servers and storage to operate."
              }
            ]
          },
          {
            "sub_topic_number": "3.4",
            "sub_topic_name": "Network hardware",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand that a computer requires a network interface card (NIC) to access a network"
              },
              {
                "objective_number": 2,
                "description": "Understand what a media access control (MAC) address is, its purpose and structure",
                "notes_and_guidance": "NICs are assigned MAC addresses at manufacture. MAC addresses are hexadecimal, combining manufacturer and serial codes."
              },
              {
                "objective_number": 3,
                "description": "Understand what an IP address is, its purpose, and its different types",
                "notes_and_guidance": "An IP address is allocated by the network and can be static or dynamic. Know the differences between IPv4 and IPv6."
              },
              {
                "objective_number": 4,
                "description": "Describe a router's role in a network",
                "notes_and_guidance": "A router directs data to its destination, assigns IP addresses, and connects a LAN to the internet."
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
                "objective_number": 1,
                "description": "Describe the difference between system software and application software, with examples",
                "notes_and_guidance": "System software runs the computer (operating systems, utilities). Application software provides user-required services."
              },
              {
                "objective_number": 2,
                "description": "Describe the role and basic functions of an operating system",
                "notes_and_guidance": "Includes: managing files, handling interrupts, providing an interface, managing peripherals/drivers, memory, multitasking, application platform, security, user accounts."
              },
              {
                "objective_number": 3,
                "description": "Understand how hardware, firmware and an operating system are all required to run application software",
                "notes_and_guidance": "Applications require the OS; OS runs on firmware; firmware (e.g., bootloader) runs on hardware."
              },
              {
                "objective_number": 4,
                "description": "Describe interrupts and how they are handled",
                "notes_and_guidance": "Includes: interrupt generation, interrupt service routines, and consequences. Software interrupts: e.g., division by zero, memory access conflict. Hardware interrupts: e.g., key presses, mouse movement."
              }
            ]
          },
          {
            "sub_topic_number": "4.2",
            "sub_topic_name": "Types of programming language, translators and integrated development environments (IDEs)",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Explain high-level and low-level languages, with their advantages and disadvantages",
                "notes_and_guidance": "Consider: readability, ease of debugging, portability, hardware manipulation."
              },
              {
                "objective_number": 2,
                "description": "Understand that assembly language is a type of low-level language using mnemonics, and requires an assembler"
              },
              {
                "objective_number": 3,
                "description": "Describe compilers and interpreters: how each translates and reports errors",
                "notes_and_guidance": "Compiler: translates all code, produces an executable, reports errors after translation. Interpreter: translates and runs code line-by-line, stops at errors."
              },
              {
                "objective_number": 4,
                "description": "Explain the advantages and disadvantages of compilers and interpreters",
                "notes_and_guidance": "Interpreters are useful in development; compilers are used for translating final versions."
              },
              {
                "objective_number": 5,
                "description": "Explain the role of an IDE and common IDE functions",
                "notes_and_guidance": "Functions: code editing, run-time, translation, error checking, auto-completion/correction, pretty printing."
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
                "objective_number": 1,
                "description": "Understand the difference between the internet and the world wide web",
                "notes_and_guidance": "The internet is the infrastructure; the web is pages/sites accessed via the internet."
              },
              {
                "objective_number": 2,
                "description": "Understand what a uniform resource locator (URL) is",
                "notes_and_guidance": "A text-based address for websites/web pages; may include protocol, domain, page/file name."
              },
              {
                "objective_number": 3,
                "description": "Describe HTTP and HTTPS: purpose and operation"
              },
              {
                "objective_number": 4,
                "description": "Explain the purpose and functions of a web browser",
                "notes_and_guidance": "Browsers render HTML and display pages. Functions include bookmarks, history, tabs, cookies, navigation tools, address bar."
              },
              {
                "objective_number": 5,
                "description": "Describe how a web page is located, retrieved and displayed after a URL is entered",
                "notes_and_guidance": "Covers web browser, IP address, DNS, web server, HTML."
              },
              {
                "objective_number": 6,
                "description": "Explain what cookies are and how they are used, including session and persistent cookies",
                "notes_and_guidance": "Cookies are used to store preferences, cart contents, login details, etc."
              }
            ]
          },
          {
            "sub_topic_number": "5.2",
            "sub_topic_name": "Digital currency",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand the concept of digital currencies and how they are used",
                "notes_and_guidance": "A digital currency exists only electronically."
              },
              {
                "objective_number": 2,
                "description": "Understand blockchain and how it tracks digital currency transactions",
                "notes_and_guidance": "Blockchain is a digital ledger: an unalterable, time-stamped series of records."
              }
            ]
          },
          {
            "sub_topic_number": "5.3",
            "sub_topic_name": "Cyber security",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Describe different cyber security threats and their purposes",
                "notes_and_guidance": "Examples: brute-force, data interception, DDoS, hacking, malware (virus, worm, trojan, spyware, adware, ransomware), pharming, phishing, social engineering."
              },
              {
                "objective_number": 2,
                "description": "Explain how different solutions can keep data safe from cyber security threats",
                "notes_and_guidance": "Measures: access levels, anti-malware, authentication, auto-updates, careful communication, checking URLs, firewalls, privacy settings, proxies, SSL."
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
                "objective_number": 1,
                "description": "Describe how sensors, microprocessors, and actuators work together in automated systems"
              },
              {
                "objective_number": 2,
                "description": "Describe advantages and disadvantages of automated systems for a given scenario",
                "notes_and_guidance": "Scenarios may include industry, transport, agriculture, weather, gaming, lighting, and science."
              }
            ]
          },
          {
            "sub_topic_number": "6.2",
            "sub_topic_name": "Robotics",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand what robotics is",
                "notes_and_guidance": "Robotics covers designing, constructing, and operating robots. Examples: factory equipment, domestic robots, drones."
              },
              {
                "objective_number": 2,
                "description": "Describe robot characteristics",
                "notes_and_guidance": "Features: mechanical structure, electrical components (e.g., sensors, microprocessors, actuators), programmability."
              },
              {
                "objective_number": 3,
                "description": "Understand the roles of robots and pros/cons of their use",
                "notes_and_guidance": "Applications: industry, transport, agriculture, medicine, home, entertainment."
              }
            ]
          },
          {
            "sub_topic_number": "6.3",
            "sub_topic_name": "Artificial intelligence",
            "learning_objectives": [
              {
                "objective_number": 1,
                "description": "Understand what artificial intelligence (AI) is",
                "notes_and_guidance": "AI is about simulating intelligent behaviour with computers."
              },
              {
                "objective_number": 2,
                "description": "Describe AI's main characteristics, including data collection/rules, reasoning, and ability to learn/adapt"
              },
              {
                "objective_number": 3,
                "description": "Explain basic operation/components of AI systems",
                "notes_and_guidance": "Covers expert systems (knowledge base, rule base, inference engine, interface) and machine learning (program adapts its processes/data automatically)."
              }
            ]
          }
        ]
      },
      {
        "syllabus_name": "Cambridge IGCSE Computer Science 0478",
        "summary_of_changes": [
          {
            "syllabus_years": "2023, 2024 and 2025",
            "changes": [
              {
                "version": "Version 2, published July 2023",
                "section": "Changes to syllabus content",
                "points": [
                  "Learning outcome 1.3.2 on page 11 has been updated. Calculations must use the measurement of 1024 and not 1000.",
                  "A minor change has been made to learning outcome 2.1.1.b on page 12 for clarity.",
                  "The abbreviation of the fetch-decode-execute (FDE) cycle has been added to learning outcome 3.1.2.b on page 14.",
                  "Learning outcome 7.5.b on page 24 has been updated to include the purpose of each verification check.",
                  "The Procedures and functions section on page 44 has been updated to clarify that procedures and functions are defined at the start of the code."
                ]
              },
              {
                "version": "Version 1, published September 2020",
                "section": "Changes to syllabus content",
                "points": [
                  "The learner attributes have been updated.",
                  "The structure of the subject content has changed to ensure a coherent topic structure.",
                  "The wording in the learning objectives has been updated to provide clarity on the depth to which each topic should be taught and a guidance column has been included.",
                  "There has been a limited amount of change to topics: some topics have been removed, such as ethics; some topics have been added, such as robotics, artificial intelligence and 2D arrays.",
                  "The teaching time still falls within the recommended guided learning hours.",
                  "Boolean logic will be assessed in Paper 2.",
                  "The learning objectives have been numbered, rather than listed by bullet points.",
                  "The Details of the assessment section has been updated and now includes flowchart symbols and logic gate symbols.",
                  "Further explanation regarding pseudocode has been provided, including a revised pseudocode guide as part of the syllabus document and not as a separate guide.",
                  "Mathematical requirements have been added to the Details of the assessment section.",
                  "A list of command words to be used in assessments has been provided."
                ]
              },
              {
                "version": "Version 1, published September 2020",
                "section": "Changes to assessment (including changes to specimen papers)",
                "points": [
                  "The syllabus aims have been updated to improve the clarity of wording.",
                  "The wording of the assessment objectives (AOs) has been updated to provide greater clarity. The analysis and design of computational or programming problems has been included in AO2, whereas analysis was previously part of AO3. These changes provide consistency with the approach at AS & A Level.",
                  "Paper 1 Theory has been renamed Paper 1 Computer Systems.",
                  "Paper 2 Problem-solving and Programming has been renamed Paper 2 Algorithms, Programming and Logic.",
                  "Paper 1 and Paper 2 are now weighted at 50%.",
                  "Paper 2 now has 75 marks.",
                  "Pre-release material will no longer be used as part of the assessment in Paper 2. This has been replaced by an unseen scenario question.",
                  "The scenario question will be worth 15 marks and will require candidates to write an algorithm in pseudocode or program code to a given scenario in the examination. It is expected that candidates will spend 30 minutes answering this question. This question will always be the final question on Paper 2."
                ]
              }
            ]
          }
        ]
      }
    ]
  }
]