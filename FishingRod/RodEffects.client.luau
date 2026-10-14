-- Effects for the fishing rods, driven by the model attributes "Rarity" and "Anim" (see STYLE_GUIDE.md).
-- The fishing line is a Beam between the rod tip and the part LineEnd, so it stretches by itself when the hook flies out.
-- Runs on each client, uses only built-in particle textures.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local rod = script.Parent
local tip = rod:WaitForChild("Tip")
local lineEnd = rod:WaitForChild("LineEnd")

-- Seconds into each animation (matches the animations).
local LAND_TIME = 0.9 -- Cast: the hook lands in the water
local JERK_TIME = 0.5 -- Catch: the rod flicks and the catch comes out
local SLACK_TIME = 0.6 -- Miss: the line goes limp
local LINE_COLOR = Color3.fromRGB(235, 240, 245)
local WATER_COLOR = Color3.fromRGB(170, 220, 250)

local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 90, 77)),
	ColorSequenceKeypoint.new(0.25, Color3.fromRGB(242, 194, 48)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(92, 214, 107)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(61, 184, 245)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(155, 107, 255)),
})

-- idleRate: sparkles per second at the tip while waiting, burst: sparkles when the catch comes out.
local RARITIES = {
	Common = { color = Color3.fromRGB(245, 245, 240), idleRate = 0, burst = 12 },
	Rare = { color = Color3.fromRGB(61, 184, 245), idleRate = 3, burst = 25 },
	Epic = { color = Color3.fromRGB(155, 107, 255), idleRate = 6, burst = 45 },
	Legendary = { color = Color3.fromRGB(242, 194, 48), idleRate = 10, burst = 70 },
	Mythic = { color = Color3.fromRGB(255, 255, 255), idleRate = 14, burst = 100, rainbow = true },
}

local rarity = rod:GetAttribute("Rarity")
local config = assert(RARITIES[rarity], rod.Name .. ": unknown Rarity " .. tostring(rarity))

local outline = Instance.new("Highlight")
outline.FillTransparency = 1
outline.OutlineColor = config.color
outline.DepthMode = Enum.HighlightDepthMode.Occluded
outline.Parent = rod

local tipPoint = Instance.new("Attachment")
tipPoint.Parent = tip
local hookPoint = Instance.new("Attachment")
hookPoint.Parent = lineEnd

local line = Instance.new("Beam")
line.Attachment0 = tipPoint
line.Attachment1 = hookPoint
line.Width0 = 0.05
line.Width1 = 0.05
line.FaceCamera = true
line.LightEmission = 0.3
line.Segments = 8
line.Color = if config.rainbow then RAINBOW else ColorSequence.new(LINE_COLOR)
line.Parent = tip

local light = Instance.new("PointLight")
light.Color = config.color
light.Range = 0
light.Parent = tipPoint

local function newEmitter(parent, color, speed, size)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Color = if config.rainbow and color == config.color then RAINBOW else ColorSequence.new(color)
	emitter.LightEmission = 1
	emitter.Rate = 0
	emitter.Lifetime = NumberRange.new(0.6, 1.2)
	emitter.Speed = NumberRange.new(speed * 0.6, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.2, size),
		NumberSequenceKeypoint.new(1, 0),
	})
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-120, 120)
	emitter.Parent = parent
	return emitter
end

local sparkles = newEmitter(tipPoint, config.color, 3, 0.4)
local burst = newEmitter(tipPoint, config.color, 14, 0.5)

-- Water droplets thrown up where the hook is.
local splash = newEmitter(hookPoint, WATER_COLOR, 10, 0.25)
splash.LightEmission = 0.2
splash.Lifetime = NumberRange.new(0.4, 0.8)
splash.SpreadAngle = Vector2.new(35, 35)
splash.EmissionDirection = Enum.NormalId.Top
splash.Acceleration = Vector3.new(0, -30, 0)

local function flash(peak)
	light.Color = config.color
	light.Range = peak
	TweenService:Create(light, TweenInfo.new(0.6), { Range = 0 }):Play()
end

local function onAnim(name)
	sparkles.Rate = if name == "Idle" then config.idleRate elseif name == "Reel" then config.idleRate + 2 else 0

	local function later(time, action)
		task.delay(time, function()
			if rod:GetAttribute("Anim") == name then
				action()
			end
		end)
	end

	if name == "Cast" then
		later(LAND_TIME, function()
			splash:Emit(14)
		end)
	elseif name == "Catch" then
		later(JERK_TIME, function()
			burst:Emit(config.burst)
			splash:Emit(10)
			flash(10)
		end)
	elseif name == "Miss" then
		later(SLACK_TIME, function()
			splash:Emit(6)
		end)
	end
end

rod:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(rod:GetAttribute("Anim"))
end)
onAnim(rod:GetAttribute("Anim"))

-- Outline pulses to call attention (Mythic cycles through the rainbow).
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	if config.rainbow then
		outline.OutlineColor = Color3.fromHSV(t / 3 % 1, 0.6, 1)
	end
	if rod:GetAttribute("Anim") == "Idle" then
		outline.OutlineTransparency = 0.5 + 0.4 * math.sin(t * 5)
	end
end)
