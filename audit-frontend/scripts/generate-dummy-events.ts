/**
 * Script to generate dummy audit events for robotics club
 * Run with: npx tsx scripts/generate-dummy-events.ts
 */

const users = [
    { id: "1", name: "Jason Antwi-Appah", email: "jason.antwi-appah@utdallas.edu" },
    { id: "2", name: "Mason Thomas", email: "mason.thomas@utdallas.edu" },
    { id: "3", name: "Gabriel Burbach", email: "gabriel.burbach@utdallas.edu" },
    { id: "4", name: "Colin Wong", email: "colin.wong@utdallas.edu" },
    { id: "5", name: "Morgan Lee", email: "morgan.lee@utdallas.edu" },
    { id: "6", name: "Natalie Stromberg", email: "natalie.stromberg@utdallas.edu" },
    { id: "7", name: "Ana Wise", email: "ana.wise@utdallas.edu" },
    { id: "8", name: "Tian Wang", email: "tian.wang@utdallas.edu" },
    { id: "9", name: "Lucas Igl", email: "lucas.igl@utdallas.edu" },
    { id: "10", name: "Dylan Bigini", email: "dylan.bigini@utdallas.edu" },
    { id: "11", name: "Dakota Moore", email: "dakota.moore@utdallas.edu" },
    { id: "12", name: "Blake Taylor", email: "blake.taylor@utdallas.edu" },
    { id: "14", name: "River Thomas", email: "river.thomas@utdallas.edu" },
];

// Tool pool - realistic robotics equipment
const tools = [
    // VEX Robotics
    { id: "1", name: "V5 Smart Motor", description: "VEX V5 5.5W smart motor with integrated encoder", type: "Motor", cost: 89.99 },
    { id: "2", name: "V5 Optical Sensor", description: "VEX V5 optical sensor for line following and color detection", type: "Sensor", cost: 24.99 },
    { id: "3", name: "V5 Inertial Sensor", description: "VEX V5 inertial sensor with 3-axis gyro and accelerometer", type: "Sensor", cost: 49.99 },
    { id: "4", name: "V5 Vision Sensor", description: "VEX V5 vision sensor for object detection and tracking", type: "Sensor", cost: 199.99 },
    { id: "5", name: "V5 Controller", description: "VEX V5 competition controller with LCD screen", type: "Controller", cost: 79.99 },
    { id: "6", name: "V5 Brain", description: "VEX V5 robot brain with ARM processor", type: "Controller", cost: 199.99 },
    { id: "7", name: "V5 Battery", description: "VEX V5 3000mAh lithium-ion battery pack", type: "Power", cost: 34.99 },
    { id: "8", name: "Omni Wheels Set", description: "Set of 4 VEX omni wheels for holonomic drive", type: "Mechanical", cost: 59.99 },
    { id: "9", name: "High Strength Chain", description: "VEX high strength chain and sprocket kit", type: "Mechanical", cost: 19.99 },
    { id: "10", name: "Aluminum C-Channel", description: "VEX aluminum C-channel structural pieces (10 pack)", type: "Structural", cost: 24.99 },
    
    // Combat Robotics
    { id: "11", name: "Turnigy SK3 Brushless Motor", description: "5055-430KV brushless motor for combat robot drive", type: "Motor", cost: 89.99 },
    { id: "12", name: "VESC 6 ESC", description: "VESC 6 electronic speed controller for brushless motors", type: "Electronics", cost: 149.99 },
    { id: "13", name: "LiPo Battery 6S 5000mAh", description: "6S 5000mAh lithium polymer battery for combat robot", type: "Power", cost: 79.99 },
    { id: "14", name: "Titanium Armor Plate", description: "3mm titanium armor plate 12x12 inches", type: "Armor", cost: 249.99 },
    { id: "15", name: "AR500 Steel Wedge", description: "AR500 hardened steel wedge for combat robot", type: "Weapon", cost: 199.99 },
    { id: "16", name: "Spinner Motor", description: "High RPM brushless motor for vertical spinner weapon", type: "Motor", cost: 299.99 },
    { id: "17", name: "Futaba Radio Controller", description: "Futaba 4PV 4-channel radio controller system", type: "Controller", cost: 199.99 },
    { id: "18", name: "Receiver Module", description: "2.4GHz receiver module for radio control", type: "Electronics", cost: 49.99 },
    { id: "19", name: "Weapon Pulley", description: "Aluminum weapon pulley for spinner mechanism", type: "Mechanical", cost: 34.99 },
    { id: "20", name: "Combat Robot Frame Kit", description: "Pre-cut aluminum frame kit for 30lb combat robot", type: "Structural", cost: 449.99 },
    
    // Mars Rover
    { id: "21", name: "Raspberry Pi Camera Module", description: "Raspberry Pi HQ camera module for rover imaging", type: "Sensor", cost: 49.99 },
    { id: "22", name: "IMU Sensor", description: "9-axis IMU sensor with accelerometer, gyro, and magnetometer", type: "Sensor", cost: 34.99 },
    { id: "23", name: "GPS Module", description: "U-blox GPS module with RTK capability", type: "Sensor", cost: 199.99 },
    { id: "24", name: "Temperature Sensor", description: "DS18B20 waterproof temperature sensor", type: "Sensor", cost: 9.99 },
    { id: "25", name: "Linear Actuator", description: "12V linear actuator 6 inch stroke 150lb force", type: "Actuator", cost: 89.99 },
    { id: "26", name: "Servo Motor", description: "High torque servo motor 20kg-cm", type: "Actuator", cost: 24.99 },
    { id: "27", name: "Solar Panel", description: "50W flexible solar panel for rover power", type: "Power", cost: 149.99 },
    { id: "28", name: "Rover Chassis", description: "6-wheel rocker-bogie chassis kit", type: "Structural", cost: 599.99 },
    { id: "29", name: "Spectrometer", description: "Miniature visible light spectrometer for soil analysis", type: "Instrument", cost: 899.99 },
    { id: "30", name: "LoRA Radio Module", description: "LoRA radio module for long-range communication", type: "Electronics", cost: 79.99 },
    { id: "31", name: "Rover Arm", description: "5-DOF robotic arm for sample collection", type: "Mechanical", cost: 799.99 },
    { id: "32", name: "LIDAR Sensor", description: "2D LIDAR sensor for obstacle detection and mapping", type: "Sensor", cost: 1299.99 },
    
    // General Shop Tools
    { id: "33", name: "3D Printer Ender 3", description: "Creality Ender 3 Pro 3D printer", type: "Fabrication", cost: 249.99 },
    { id: "34", name: "Laser Cutter", description: "40W CO2 laser cutter/engraver", type: "Fabrication", cost: 3499.99 },
    { id: "35", name: "Soldering Station", description: "Hakko FX888D digital soldering station", type: "Electronics", cost: 99.99 },
    { id: "36", name: "Digital Multimeter", description: "Fluke 87V digital multimeter", type: "Test Equipment", cost: 399.99 },
    { id: "37", name: "Oscilloscope", description: "Rigol DS1054Z 50MHz digital oscilloscope", type: "Test Equipment", cost: 399.99 },
    { id: "38", name: "Drill Press", description: "10-inch benchtop drill press", type: "Fabrication", cost: 199.99 },
    { id: "39", name: "CNC Router", description: "3018 Pro CNC router kit", type: "Fabrication", cost: 299.99 },
    { id: "40", name: "Heat Gun", description: "2000W variable temperature heat gun", type: "Tool", cost: 34.99 },
    { id: "41", name: "Dremel Tool", description: "Dremel 3000 rotary tool kit", type: "Tool", cost: 79.99 },
    { id: "42", name: "Wire Strippers", description: "Automatic wire stripper and cutter", type: "Tool", cost: 24.99 },
    { id: "43", name: "Calipers", description: "Digital calipers 0-6 inch with LCD display", type: "Tool", cost: 19.99 },
    { id: "44", name: "Hot Glue Gun", description: "High temperature hot glue gun", type: "Tool", cost: 14.99 },
    { id: "45", name: "Jigsaw", description: "Cordless jigsaw with variable speed", type: "Tool", cost: 89.99 },
    { id: "46", name: "Angle Grinder", description: "4.5 inch angle grinder", type: "Tool", cost: 49.99 },
    { id: "47", name: "Bench Vise", description: "6 inch bench vise with swivel base", type: "Tool", cost: 79.99 },
    { id: "48", name: "Power Supply", description: "Variable DC power supply 0-30V 0-5A", type: "Test Equipment", cost: 89.99 },
    { id: "49", name: "Function Generator", description: "Signal generator 0.1Hz-20MHz", type: "Test Equipment", cost: 199.99 },
    { id: "50", name: "Logic Analyzer", description: "8-channel USB logic analyzer", type: "Test Equipment", cost: 149.99 },
    { id: "51", name: "Arduino Uno", description: "Arduino Uno R3 microcontroller board", type: "Electronics", cost: 24.99 },
    { id: "52", name: "Raspberry Pi 4", description: "Raspberry Pi 4 Model B 4GB", type: "Electronics", cost: 55.00 },
    { id: "53", name: "Breadboard Kit", description: "Solderless breadboard kit with jumper wires", type: "Electronics", cost: 19.99 },
    { id: "54", name: "Screwdriver Set", description: "Precision screwdriver set with 40 bits", type: "Tool", cost: 29.99 },
    { id: "55", name: "Wrench Set", description: "Metric and SAE combination wrench set", type: "Tool", cost: 39.99 },
    { id: "56", name: "Allen Key Set", description: "Hex key set metric and imperial", type: "Tool", cost: 14.99 },
    { id: "57", name: "Safety Glasses", description: "ANSI Z87.1 safety glasses (10 pack)", type: "Safety", cost: 24.99 },
    { id: "58", name: "Workbench", description: "Heavy duty workbench 48x24 inches", type: "Furniture", cost: 199.99 },
    { id: "59", name: "Tool Chest", description: "5-drawer tool chest with lock", type: "Furniture", cost: 299.99 },
    { id: "60", name: "First Aid Kit", description: "Industrial first aid kit", type: "Safety", cost: 49.99 },
];

const randomImageUrl = "https://picsum.photos/500";

// Helper function to get random item from array
function randomItem<T>(array: T[]): T {
    return array[Math.floor(Math.random() * array.length)];
}

// Helper function to get random number in range
function randomInt(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Helper function to escape quotes in strings
function escapeString(str: string): string {
    return str.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

// Generate timestamp within last 14 days
// More events during weekdays (Mon-Fri), fewer on weekends
function generateTimestamp(): number {
    const now = Date.now() / 1000; // Current time in seconds
    
    // Generate random day (0-13 days ago)
    let daysAgo = Math.random() * 14;
    
    // Bias towards weekdays (70% chance of weekday)
    const targetDate = new Date((now - daysAgo * 24 * 60 * 60) * 1000);
    let dayOfWeek = targetDate.getDay();
    
    // If it's a weekend, bias towards moving to weekday
    if ((dayOfWeek === 0 || dayOfWeek === 6) && Math.random() < 0.7) {
        // Move to Friday if Saturday, or Monday if Sunday
        if (dayOfWeek === 6) {
            daysAgo = Math.max(0, daysAgo - 1);
        } else {
            daysAgo = Math.min(13, daysAgo + 1);
        }
    }
    
    // Random time within that day (8 AM to 10 PM for more realistic hours)
    const hours = randomInt(8, 22);
    const minutes = randomInt(0, 59);
    const seconds = randomInt(0, 59);
    
    const timestamp = now - (daysAgo * 24 * 60 * 60) - (hours * 60 * 60) - (minutes * 60) - seconds;
    
    return Math.floor(timestamp);
}

// Generate events
function generateEvents(): string {
    const events = [];
    const eventCount = randomInt(200, 300);
    
    for (let i = 1; i <= eventCount; i++) {
        const user = randomItem(users);
        const tool = randomItem(tools);
        const eventType = Math.random() < 0.5 ? "tool_checkin" : "tool_checkout";
        const timestamp = generateTimestamp();
        
        // Generate unique image URLs with different seeds
        const imageSeed = randomInt(1, 1000);
        const userImageUrl = `https://picsum.photos/seed/user${user.id}${imageSeed}/500`;
        const toolImageUrl = `https://picsum.photos/seed/tool${tool.id}${imageSeed}/500`;
        const eventImageUrl = `https://picsum.photos/seed/event${i}${imageSeed}/500`;
        
        const event = {
            id: String(i + 1), // Start from 2 since there's already event "1"
            timestamp,
            type: eventType,
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                imageUrl: userImageUrl,
            },
            tool: {
                id: tool.id,
                name: tool.name,
                description: tool.description,
                imageUrl: toolImageUrl,
                type: tool.type,
                cost: tool.cost,
            },
            eventImageUrl,
        };
        
        events.push(event);
    }
    
    // Sort events by timestamp (newest first)
    events.sort((a, b) => b.timestamp - a.timestamp);
    
    // Format as TypeScript code
    let output = "export const dummyEvents: Event[] = [\n";
    
    events.forEach((event, index) => {
        output += "    {\n";
        output += `        id: "${event.id}",\n`;
        output += `        timestamp: ${event.timestamp},\n`;
        output += `        type: "${event.type}",\n`;
        output += "        user: {\n";
        output += `            id: "${event.user.id}",\n`;
        output += `            name: "${escapeString(event.user.name)}",\n`;
        output += `            email: "${escapeString(event.user.email)}",\n`;
        output += `            imageUrl: "${event.user.imageUrl}",\n`;
        output += "        },\n";
        output += "        tool: {\n";
        output += `            id: "${event.tool.id}",\n`;
        output += `            name: "${escapeString(event.tool.name)}",\n`;
        output += `            description: "${escapeString(event.tool.description)}",\n`;
        output += `            imageUrl: "${event.tool.imageUrl}",\n`;
        output += `            type: "${event.tool.type}",\n`;
        output += `            cost: ${event.tool.cost},\n`;
        output += "        },\n";
        output += `        eventImageUrl: "${event.eventImageUrl}",\n`;
        output += "    }";
        
        if (index < events.length - 1) {
            output += ",";
        }
        output += "\n";
    });
    
    output += "];\n";
    
    return output;
}

// Main execution
const output = generateEvents();
console.log(output);

