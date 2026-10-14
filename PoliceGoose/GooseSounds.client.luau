-- Plays a sound for each goose action, driven by the model attribute "Anim".
-- Upload the WAV files in Sounds/ to Roblox, then paste the ids below as "rbxassetid://123456".
-- An empty id is skipped, so the goose works silently until the sounds are uploaded.
-- "period" is how often a looped animation repeats its sound (matches the animation length or step rate);
-- animations without a period play once when they start.

local SOUNDS = {
	Idle = { id = "", volume = 0.4, period = 6 },
	Walk = { id = "", volume = 0.4, period = 0.5 },
	Run = { id = "", volume = 0.5, period = 0.22 },
	Fly = { id = "", volume = 0.5, period = 0.5 },
	Attack = { id = "", volume = 0.8, period = 0.7 },
	Sleep = { id = "", volume = 0.5, period = 3 },
	Search = { id = "", volume = 0.4, period = 2.4 },
	Faint = { id = "", volume = 0.7 },
	Alert = { id = "", volume = 0.7 },
	Whistle = { id = "", volume = 0.8 },
	Stunned = { id = "", volume = 0.8 },
	Threaten = { id = "", volume = 0.8 },
}

local goose = script.Parent
local root = goose:WaitForChild("HumanoidRootPart")

local function play(entry)
	local sound = Instance.new("Sound")
	sound.SoundId = entry.id
	sound.Volume = entry.volume
	sound.RollOffMaxDistance = 80
	sound.Parent = root
	sound.Ended:Once(function()
		sound:Destroy()
	end)
	sound:Play()
end

local run = 0

local function onAnim(name)
	run += 1
	local thisRun = run
	local entry = SOUNDS[name]
	if not entry or entry.id == "" then
		return
	end
	if not entry.period then
		play(entry)
		return
	end
	task.spawn(function()
		while run == thisRun do
			play(entry)
			task.wait(entry.period)
		end
	end)
end

goose:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(goose:GetAttribute("Anim"))
end)
onAnim(goose:GetAttribute("Anim"))
