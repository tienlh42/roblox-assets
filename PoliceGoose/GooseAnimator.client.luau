-- Plays the KeyframeSequences in the "Animations" folder by writing Motor6D.Transform directly,
-- so no animation upload is needed. Runs on each client (RunContext = Client) because
-- Motor6D.Transform does not replicate. Change the model attribute "Anim" to switch animation.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local FADE_TIME = 0.15
local EASING_STYLES = {
	Linear = Enum.EasingStyle.Linear,
	Cubic = Enum.EasingStyle.Cubic,
	CubicV2 = Enum.EasingStyle.Cubic,
	Elastic = Enum.EasingStyle.Elastic,
	Bounce = Enum.EasingStyle.Bounce,
}

local goose = script.Parent

local motors = {}
for _, descendant in goose:GetDescendants() do
	if descendant:IsA("Motor6D") then
		motors[descendant.Part1.Name] = descendant
	end
end

local function loadAnimation(sequence)
	local keyframes = sequence:GetKeyframes()
	table.sort(keyframes, function(a, b)
		return a.Time < b.Time
	end)

	local tracks = {}
	for _, keyframe in keyframes do
		for _, pose in keyframe:GetDescendants() do
			if pose:IsA("Pose") and motors[pose.Name] then
				tracks[pose.Name] = tracks[pose.Name] or {}
				table.insert(tracks[pose.Name], {
					time = keyframe.Time,
					cframe = pose.CFrame,
					style = pose.EasingStyle.Name,
					direction = Enum.EasingDirection[pose.EasingDirection.Name],
				})
			end
		end
	end

	return { tracks = tracks, length = keyframes[#keyframes].Time, looped = sequence.Loop }
end

local animations = {}
for _, sequence in goose:WaitForChild("Animations"):GetChildren() do
	animations[sequence.Name] = loadAnimation(sequence)
end

local function sample(track, t)
	for i = 1, #track - 1 do
		local from, to = track[i], track[i + 1]
		if t < to.time then
			if from.style == "Constant" then
				return from.cframe
			end
			local alpha = math.max(t - from.time, 0) / (to.time - from.time)
			alpha = TweenService:GetValue(alpha, EASING_STYLES[from.style], from.direction)
			return from.cframe:Lerp(to.cframe, alpha)
		end
	end
	return track[#track].cframe
end

local current
local startTime
local fadeFrom = {}

local function play(name)
	current = animations[name]
	assert(current, goose.Name .. ": unknown animation " .. tostring(name))
	for jointName, motor in motors do
		fadeFrom[jointName] = motor.Transform
	end
	startTime = os.clock()
end

goose:GetAttributeChangedSignal("Anim"):Connect(function()
	play(goose:GetAttribute("Anim"))
end)
play(goose:GetAttribute("Anim"))

RunService.PreSimulation:Connect(function()
	local elapsed = os.clock() - startTime
	local t = if current.looped then elapsed % current.length else math.min(elapsed, current.length)
	local fade = math.min(elapsed / FADE_TIME, 1)
	for jointName, motor in motors do
		local track = current.tracks[jointName]
		local target = if track then sample(track, t) else CFrame.identity
		motor.Transform = fadeFrom[jointName]:Lerp(target, fade)
	end
end)
