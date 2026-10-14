-- Effects for the pets, driven by the model attributes "Rarity" and "Anim" (see STYLE_GUIDE.md).
-- Runs on each client, uses only built-in particle textures. The same script serves all six pets.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local pet = script.Parent
local root = pet:WaitForChild("HumanoidRootPart")

-- Seconds into each animation (matches the animations).
local BONK_TIME = 0.45 -- Attack (loops every 0.8 s): the head hits
local HURT_TIME = 0.15 -- Hurt: the pet is pushed back
local EXHAUST_TIME = 0.9 -- Exhausted: the pet sits down and the bubble grows
local HAPPY_TIME = 0.5 -- Happy: the jump
local JOB_TIME = 0.8 -- Job: the key moment of the trade
local ATTACK_PERIOD = 0.8
local HALO_SPEED = 1.6 -- radians per second
local STAR_COLOR = Color3.fromRGB(255, 225, 90)
local HEART_COLOR = Color3.fromRGB(255, 111, 181)
local BUBBLE_COLOR = Color3.fromRGB(190, 225, 255)

local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 90, 77)),
	ColorSequenceKeypoint.new(0.25, Color3.fromRGB(242, 194, 48)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(92, 214, 107)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(61, 184, 245)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(155, 107, 255)),
})

-- idleRate: sparkles per second around the pet, burst: sparkles for the happy jump and the job.
local RARITIES = {
	Common = { color = Color3.fromRGB(245, 245, 240), idleRate = 0, burst = 8 },
	Rare = { color = Color3.fromRGB(61, 184, 245), idleRate = 2, burst = 14 },
	Epic = { color = Color3.fromRGB(155, 107, 255), idleRate = 4, burst = 22 },
	Legendary = { color = Color3.fromRGB(242, 194, 48), idleRate = 6, burst = 32 },
	Mythic = { color = Color3.fromRGB(255, 255, 255), idleRate = 9, burst = 45, rainbow = true },
}

local rarity = pet:GetAttribute("Rarity")
local config = assert(RARITIES[rarity], pet.Name .. ": unknown Rarity " .. tostring(rarity))

-- The root is 1 stud at design size, so its size gives the scale of this pet (bigger for rarer pets).
local scale = root.Size.Y
local ROOT_HEIGHT = 0.9 * scale -- height of the root center above the ground

local outline = Instance.new("Highlight")
outline.FillTransparency = 1
outline.OutlineColor = config.color
outline.DepthMode = Enum.HighlightDepthMode.Occluded
outline.Parent = pet

-- Emitters sit on attachments of the root (y is the height above the ground, z - is the front).
local function attachmentAt(y, z)
	local attachment = Instance.new("Attachment")
	attachment.Position = Vector3.new(0, y * scale - ROOT_HEIGHT, z * scale)
	attachment.Parent = root
	return attachment
end

local bodyPoint = attachmentAt(1.5, 0)
local headPoint = attachmentAt(2.3, -0.9)
local topPoint = attachmentAt(3.2, 0)

local function newEmitter(parent, color, speed, size)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Color = if config.rainbow and color == config.color then RAINBOW else ColorSequence.new(color)
	emitter.LightEmission = 1
	emitter.Rate = 0
	emitter.Lifetime = NumberRange.new(0.5, 1)
	emitter.Speed = NumberRange.new(speed * 0.6, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.2, size * scale),
		NumberSequenceKeypoint.new(1, 0),
	})
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-120, 120)
	emitter.Parent = parent
	return emitter
end

local sparkles = newEmitter(bodyPoint, config.color, 3, 0.35)
local confetti = newEmitter(topPoint, config.color, 8, 0.4)
local stars = newEmitter(headPoint, STAR_COLOR, 8, 0.4)
local hearts = newEmitter(topPoint, HEART_COLOR, 6, 0.5)

local function findHalo()
	for _, descendant in pet:GetDescendants() do
		if descendant:IsA("Weld") and descendant.Part1 and descendant.Part1.Name == "Halo" then
			return { weld = descendant, c0 = descendant.C0 }
		end
	end
	return nil
end

local halo = findHalo()
local bubble = nil
local run = 0

local function popBubble()
	if bubble then
		bubble:Destroy()
		bubble = nil
	end
end

local function showBubble()
	popBubble()
	bubble = Instance.new("Part")
	bubble.Shape = Enum.PartType.Ball
	bubble.Anchored = true
	bubble.CanCollide = false
	bubble.CanQuery = false
	bubble.Material = Enum.Material.Glass
	bubble.Color = BUBBLE_COLOR
	bubble.Transparency = 0.55
	bubble.Size = Vector3.one * 0.3
	bubble.CFrame = root.CFrame * CFrame.new(0, 0.4 * scale, 0)
	bubble.Parent = pet
	local size = 3.6 * scale
	TweenService:Create(bubble, TweenInfo.new(0.6, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
		Size = Vector3.one * size,
	}):Play()
end

local function onAnim(name)
	run += 1
	local thisRun = run
	sparkles.Rate = if name == "Idle" or name == "Walk" or name == "Run" then config.idleRate else 0
	if name ~= "Exhausted" then
		popBubble()
	end

	local function later(time, action)
		task.delay(time, function()
			if run == thisRun then
				action()
			end
		end)
	end

	if name == "Attack" then
		task.spawn(function()
			task.wait(BONK_TIME)
			while run == thisRun do
				stars:Emit(6)
				task.wait(ATTACK_PERIOD)
			end
		end)
	elseif name == "Hurt" then
		later(HURT_TIME, function()
			stars:Emit(8)
		end)
	elseif name == "Exhausted" then
		later(EXHAUST_TIME, showBubble)
	elseif name == "Happy" then
		later(HAPPY_TIME, function()
			hearts:Emit(8)
			confetti:Emit(config.burst)
		end)
	elseif name == "Job" then
		later(JOB_TIME, function()
			confetti:Emit(config.burst)
		end)
	end
end

pet:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(pet:GetAttribute("Anim"))
end)
onAnim(pet:GetAttribute("Anim"))

-- Outline pulses to call attention (Mythic cycles through the rainbow); the halo (tilted ring) turns around the vertical
-- axis; the bubble follows the pet.
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	local anim = pet:GetAttribute("Anim")
	if config.rainbow then
		outline.OutlineColor = Color3.fromHSV(t / 3 % 1, 0.6, 1)
	end
	if anim == "Idle" then
		outline.OutlineTransparency = 0.5 + 0.4 * math.sin(t * 5)
	end
	if halo then
		halo.weld.C0 = CFrame.Angles(0, t * HALO_SPEED, 0) * halo.c0
	end
	if bubble then
		bubble.CFrame = root.CFrame * CFrame.new(0, 0.4 * scale, 0)
	end
end)
